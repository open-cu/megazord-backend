import json

import requests
from bs4 import BeautifulSoup
from django.shortcuts import get_object_or_404
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from github import Auth, Github
from ninja import File, Router, UploadedFile
from pypdf import PdfReader

from accounts.models import Account
from hackathons.models import Hackathon
from megazord.api.auth import AuthBearer
from megazord.api.requests import APIRequest

from .models import HardSkillTag, Resume, SoftSkillTag
from .schemas import Error, ResumeSuggestion, SuggestResumeSchema
from .schemas import Resume as ResumeSchema

router = Router()
GIGA_TOKEN = "MGRhZWE5YjQtOTA1OC00NWM5LTliMTMtODAzZDBjZWY3MmRhOmExN2JiZTE0LWFmYjEtNDNhNS05MTFhLTg4ZGQ4YjQ4MmI5ZA=="
GITHUB_TOKEN = "XXX"


@router.post(
    "/create/custom",
    response={201: ResumeSchema, 401: Error, 400: Error, 404: Error, 409: Error},
    auth=AuthBearer(),
)
def create_resume_custom(request: APIRequest, resume: ResumeSchema):
    hackathon = get_object_or_404(Hackathon, id=resume.hackathon_id)
    account = request.user
    resume_found = Resume.objects.filter(user=account, hackathon=hackathon)
    if len(list(resume_found)) > 0:
        return 409, {"details": "Resume already exists"}
    resume_created = Resume.objects.create(
        bio=resume.bio, hackathon=hackathon, user=account
    )
    if resume.tech is not None:
        for tag in resume.tech:
            HardSkillTag.objects.create(resume=resume_created, tag_text=tag)
    if resume.soft is not None:
        for tag in resume.soft:
            SoftSkillTag.objects.create(resume=resume_created, tag_text=tag)
    if resume.github != "":
        resume_created.github = resume.github
        resume_created.save()
    if resume.hh != "":
        resume_created.hhru = resume.hh
        resume_created.save()
    if resume.telegram != "":
        resume_created.telegram = resume.telegram
        resume_created.save()
    if resume.personal_website != "":
        account = get_object_or_404(Account, id=account.id)
        resume_created.user = account
        resume_created.save()
    result = resume.dict().copy()
    return 201, result


@router.post(
    "/create/pdf",
    response={201: ResumeSchema, 401: Error, 400: Error, 404: Error, 409: Error},
    auth=AuthBearer(),
)
def create_resume_pdf_upload(
    request: APIRequest, resume: ResumeSchema, pdf: UploadedFile = File(...)
):
    hackathon = get_object_or_404(Hackathon, id=resume.hackathon_id)
    account = request.user
    resume_created = Resume.objects.filter(user=account, hackathon=hackathon)
    result = {}
    resume_created.pdf.save(pdf.name, pdf)
    result["pdf_link"] = resume_created.pdf
    result["bio"] = resume_created.bio
    result["hackathon_id"] = resume_created.hackathon.id
    result["github"] = resume_created.github
    result["hh"] = resume_created.hhru
    result["telegram"] = resume_created.telegram
    result["personal_website"] = resume_created.personal_website
    result["pdf_link"] = resume_created.pdf
    techs = HardSkillTag.objects.filter(resume=resume_created)
    ss = SoftSkillTag.objects.filter(resume=resume_created)
    hards = []
    softs = []
    for tech in techs:
        hards.append(tech.tag_text)
    for soft in ss:
        softs.append(soft.tag_text)
    result["tech"] = hards
    result["soft"] = softs
    return 200, result


@router.get(
    "/get",
    response={200: ResumeSchema, 401: Error, 400: Error, 404: Error},
    auth=AuthBearer(),
)
def get_resume(request: APIRequest, user_id: int, hackathon_id: int):
    user = get_object_or_404(Account, id=user_id)
    hackathon = get_object_or_404(Hackathon, id=hackathon_id)
    resume = get_object_or_404(Resume, user=user, hackathon=hackathon)
    result = {}
    result["id"] = resume.id
    result["bio"] = resume.bio
    result["hackathon_id"] = resume.hackathon.id
    result["github"] = resume.github
    result["hh"] = resume.hhru
    result["telegram"] = resume.telegram
    result["personal_website"] = resume.personal_website
    result["pdf_link"] = resume.pdf
    techs = HardSkillTag.objects.filter(resume=resume)
    ss = SoftSkillTag.objects.filter(resume=resume)
    hards = []
    softs = []
    for tech in techs:
        hards.append(tech.tag_text)
    for soft in ss:
        softs.append(soft.tag_text)
    result["tech"] = hards
    result["soft"] = softs
    return 200, result


@router.patch(
    "/edit",
    response={200: ResumeSchema, 401: Error, 400: Error, 404: Error},
    auth=AuthBearer(),
)
def edit_resume(request: APIRequest, resume: ResumeSchema):
    hackathon = get_object_or_404(Hackathon, id=resume.hackathon_id)
    account = request.user
    resume_created = get_object_or_404(Resume, user=account, hackathon=hackathon)
    if resume.tech is not None:
        HardSkillTag.objects.filter(resume=resume_created).delete()
        for tag in resume.tech:
            HardSkillTag.objects.create(resume=resume_created, tag_text=tag)
    if resume.soft is not None:
        SoftSkillTag.objects.filter(resume=resume_created).delete()
        for tag in resume.soft:
            SoftSkillTag.objects.create(resume=resume_created, tag_text=tag)
    if resume.github != "":
        resume_created.github = resume.github
        resume_created.save()
    if resume.bio != "":
        resume_created.bio = resume.bio
        resume_created.save()
    if resume.hh != "":
        resume_created.hhru = resume.hh
        resume_created.save()
    if resume.telegram != "":
        resume_created.telegram = resume.telegram
        resume_created.save()
    if resume.personal_website != "":
        resume_created.personal_website = resume.personal_website
        resume_created.save()
    result = resume.dict().copy()
    return 200, result


@router.post(
    "/suggest-resume-hh",
    response={200: ResumeSuggestion, 401: Error, 400: Error, 404: Error},
    auth=AuthBearer(),
)
def suggestResumeHH(request: APIRequest, hh_link: SuggestResumeSchema):
    cookies = {
        "__ddg1_": "3iIGwdHMyTVm9wz3yClZ",
        "hhtoken": "XXX",
        "hhuid": "UZm5g3ww76OapWYKwtkwRA--",
        "_xsrf": "31cd88f8a95799df7d7641102c68790a",
        "hhrole": "anonymous",
        "regions": "1",
        "region_clarified": "NOT_SET",
        "display": "desktop",
        "crypted_hhuid": "F1631BDEF3A232AC264A90F128EFECB97D3667A1F7A0B397ADCE8D949E38235F",
        "GMT": "3",
        "tmr_lvid": "e54c7bfe2d984ba8340aa554b02f6342",
        "tmr_lvidTS": "1711981491643",
        "_ym_uid": "1711981492415424170",
        "_ym_d": "1711981492",
        "_ym_isad": "1",
        "iap.uid": "713458d9f70b4f01812637b43eebe41e",
        "total_searches": "2",
        "_ga": "GA1.2.738586880.1711982128",
        "_gid": "GA1.2.968465436.1711982128",
        "supernova_user_type": "employer",
        "tmr_detect": "1%7C1711982151486",
        "__zzatgib-w-hh": "MDA0dC0jViV+FmELHw4/aQsbSl1pCENQGC9LXy8pPGpTaH1dIUdWUQkmH0QxJSMJPTxeREl0d1w7aE9jOVURCxIXRF5cVWl1FRpLSiVueCplJS0xViR8SylEXE56LiETeHAkWA8OVy8NPjteLW8PKhMjZHYhP05yhS6wzQ==",
        "gsscgib-w-hh": "vn+zRVmAKAcId7K4yGERJA5pihDV9HbRkSIUWAp1OAkrXVb1Lrd3T+cuWwQjeZwSL6zM9lCgBlO0OQrh4It8HcOE4SyG2dSffPcKLoQpB24XJV/rWOuYCh8Hf1w32dsoiPWFb1HMY7JoIR5GN8oQgH0ckYbO5/CvbQV0kF0bszSNWC17gUNr2qZLgeekwkdNilVoBeLCIG3tjpuSBxTtzELI99/uuztokpqr5c39VEgpTkG733ckyk/p1krwoA==",
        "cfidsgib-w-hh": "mTj+I+pLwFyAB4rjnoaTiUg+Xz+3mh2aJNGUbjfmgwZC9kAR82jweN7Hzu5TaqVBvc9mFU4AfdHwkPah8Co58MuccH4+ssrkvhqrE9c9Yo8kTiGT3Rv0CmgM1Krf6kJiBHA98KtovPDJ4g+NJp6oYtN3V4Yog+6/8e3ybg==",
        "device_magritte_breakpoint": "s",
        "device_breakpoint": "s",
        "fgsscgib-w-hh": "hZ9gdee09e411d8c7771b8f90c50a05cd132a53e",
    }

    headers = {
        "authority": "hh.ru",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "referer": "https://hh.ru/search/resume",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    response = requests.get(
        hh_link.link,
        cookies=cookies,
        headers=headers,
    )
    bs = BeautifulSoup(response.text)
    giga_chat = GigaChat(credentials=GIGA_TOKEN, verify_ssl_certs=False)
    data = (
        giga_chat.chat(
            "Я тебе предоствалю резюме из hh.ru, тебе нужно вычленить из него хард-скилы, софт-скилы, bio. Резюме: "
            + bs.text
            + ' Результат верни в формате JSON-списка без каких-либо пояснений, например, {"bio": "bio", "hards": ["skill1"], "softs": ["skill1"]}. Не повторяй фразы из примера и не дублируй фразы.'
        )
        .choices[0]
        .message.content
    )
    data = json.loads(data)
    return 200, data


@router.post(
    "/suggest-resume-github",
    response={200: ResumeSuggestion, 401: Error, 400: Error, 404: Error},
    auth=AuthBearer(),
)
def suggestResumeGithub(request: APIRequest, git_link: SuggestResumeSchema):
    username = git_link.link.replace("https://github.com/", "")
    username = username.replace("github.com/", "")
    username = username.replace("github.com", "")
    auth = Auth.Token(GITHUB_TOKEN)
    g = Github(auth=auth)
    languages = []
    resume = {}
    user = g.get_user(username)
    resume["bio"] = user.bio
    repos = user.get_repos()
    for repo in repos:
        if repo.language and repo.language not in languages:
            languages.append(repo.language)
    resume["hards"] = languages
    return 200, resume


@router.post(
    "/suggest-resume-pdf",
    response={200: ResumeSuggestion, 401: Error, 400: Error, 404: Error},
    auth=AuthBearer(),
)
def suggestResumePdf(request: APIRequest, pdf: UploadedFile = File(...)):
    try:
        text = ""
        reader = PdfReader(pdf)
        for page in reader.pages:
            text += page.extract_text()
        payload = Chat(
            messages=[
                Messages(
                    role=MessagesRole.USER,
                    content="Я тебе предоствалю резюме, тебе нужно вычленить из него хард-скилы, софт-скилы, bio. Резюме: "
                    + text
                    + ' Результат верни в формате JSON-списка без каких-либо пояснений, например, {"bio": "bio", "hards": ["skill1"], "softs": ["skill1"]}. Не повторяй фразы из примера и не дублируй фразы. Напиши кратко, только самое основное (не больше 2000 символов).',
                )
            ],
            max_tokens=512,
        )
        with GigaChat(credentials=GIGA_TOKEN, verify_ssl_certs=False) as giga:
            data = giga.chat(payload).choices[0].message.content
            data = json.loads(data)
            return 200, data
    except Exception:
        return 400, {"details": "Резюме слишком большое"}
