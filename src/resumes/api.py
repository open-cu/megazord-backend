import json
import re
import uuid

import httpx
from aiogithubapi import GitHubAPI
from bs4 import BeautifulSoup
from django.http import Http404
from django.shortcuts import aget_object_or_404
from faker import Faker
from flags.decorators import flag_check
from gigachat import GigaChat
from gigachat.exceptions import GigaChatException
from gigachat.models import Chat, Messages, MessagesRole
from ninja import File, Router, UploadedFile
from pypdf import PdfReader

from hackathons.models import Hackathon
from megazord.api.codes import ERROR_CODES
from megazord.api.requests import APIRequest
from megazord.schemas import ErrorSchema

from .entities import ResumeEntity
from .models import Resume
from .schemas import (
    LinkSchema,
    ResumeCreateSchema,
    ResumeSchema,
    ResumeSuggestionSchema,
    ResumeUpdateSchema,
)

router = Router()


@router.post(
    path="/create/custom", response={201: ResumeSchema, ERROR_CODES: ErrorSchema}
)
async def create_custom_resume(
    request: APIRequest, create_schema: ResumeCreateSchema
) -> tuple[int, ResumeEntity]:
    hackathon = await aget_object_or_404(
        Hackathon, id=create_schema.hackathon_id, status=Hackathon.Status.STARTED
    )
    resume = await Resume.objects.acreate(
        hackathon=hackathon,
        user=request.user,
        **create_schema.dict(exclude=["hackathon_id", "tech", "soft"]),
    )
    for soft in create_schema.soft:
        await resume.soft_skills.acreate(tag_text=soft)
    for tech in create_schema.tech:
        await resume.hard_skills.acreate(tag_text=tech)

    return 201, await resume.to_entity()


@router.get(path="/get", response={200: ResumeSchema, ERROR_CODES: ErrorSchema})
async def get_resume(
    request: APIRequest, hackathon_id: uuid.UUID, user_id: uuid.UUID
) -> ResumeEntity:
    resume = await aget_object_or_404(Resume, user=user_id, hackathon_id=hackathon_id)

    return await resume.to_entity()


@router.patch(path="/edit", response={200: ResumeSchema, ERROR_CODES: ErrorSchema})
async def edit_resume(
    request: APIRequest, update_schema: ResumeUpdateSchema
) -> ResumeEntity:
    resume = await aget_object_or_404(
        Resume,
        user=request.user,
        hackathon_id=update_schema.hackathon_id,
        hackathon__status=Hackathon.Status.STARTED,
    )
    updated_fields = update_schema.dict(
        exclude_unset=True, exclude=["hackathon_id", "tech", "soft"]
    )
    for attr, value in updated_fields.items():
        setattr(resume, attr, value)
    await resume.asave()

    await resume.soft_skills.all().adelete()
    await resume.hard_skills.all().adelete()
    for soft in update_schema.soft:
        await resume.soft_skills.acreate(tag_text=soft)
    for tech in update_schema.tech:
        await resume.hard_skills.acreate(tag_text=tech)

    return await resume.to_entity()


@router.post(
    "/suggest-resume-github",
    response={200: ResumeSuggestionSchema, ERROR_CODES: ErrorSchema},
)
async def suggest_resume_github(request: APIRequest, link_schema: LinkSchema):
    if match := re.search(pattern=r"/github\.com/([^/]+)", string=link_schema.link):
        username = match.group(1)
    else:
        username = link_schema.link

    async with GitHubAPI() as gh_api:
        gh_user = await gh_api.users.get(username=username)
        repos = await gh_api.users.repos(username=username)

    languages = {repo.language for repo in repos.data if repo.language}

    return ResumeSuggestionSchema(bio=gh_user.data.bio, hards=list(languages))


@router.post(
    path="/suggest-resume-hh",
    response={200: ResumeSuggestionSchema, ERROR_CODES: ErrorSchema},
)
async def suggest_resume_hh(
    request: APIRequest, link_schema: LinkSchema
) -> ResumeSuggestionSchema:
    headers = {"user-agent": Faker().user_agent()}
    response = httpx.get(url=link_schema.link, headers=headers)
    if response.status_code != 200:
        raise Http404

    soup = BeautifulSoup(response.text, "html.parser")
    bio = soup.find(attrs={"data-qa": "resume-block-skills-content"}).text
    skills_table = soup.find("div", {"data-qa": "skills-table"})
    skills = skills_table.find_all("span", {"data-qa": "bloko-tag__text"})

    return ResumeSuggestionSchema(bio=bio, hards=[skill.text for skill in skills])


@router.post(
    path="/suggest-resume-pdf",
    response={200: ResumeSuggestionSchema, ERROR_CODES: ErrorSchema},
    include_in_schema=False,
)
@flag_check("SUGGEST_RESUME_PDF", True)
async def suggest_resume_pdf(request: APIRequest, pdf: UploadedFile = File(...)):
    try:
        text = ""
        reader = PdfReader(pdf.read())
        for page in reader.pages:
            text += page.extract_text()
        payload = Chat(
            messages=[
                Messages(
                    role=MessagesRole.USER,
                    content="Я тебе предоствалю резюме, тебе нужно вычленить из него хард-скилы, софт-скилы, bio. "
                    f"Резюме: {text} Результат верни в формате JSON-списка без каких-либо пояснений, "
                    'например, {"bio": "bio", "hards": ["skill1"], "softs": ["skill1"]}. '
                    "Не повторяй фразы из примера и не дублируй фразы. "
                    "Напиши кратко, только самое основное (не больше 2000 символов).",
                )
            ],
            max_tokens=512,
        )
        async with GigaChat(credentials="GIGA_TOKEN", verify_ssl_certs=False) as giga:
            data = await giga.achat(payload)
            data = data.choices[0].message.content
            data = json.loads(data)
            return 200, data
    except GigaChatException:
        return 400, ErrorSchema(detail="Резюме слишком большое")
