import uuid
from datetime import datetime

import jwt
from django.db.models import Count
from django.shortcuts import aget_object_or_404
from ninja import Router

from accounts.models import Account
from hackathons.models import Hackathon
from hackathons.schemas import HackathonSummarySchema
from megazord.api.codes import ERROR_CODES
from megazord.api.requests import APIRequest
from megazord.schemas import ErrorSchema, StatusSchema
from megazord.settings import FRONTEND_URL, SECRET_KEY
from profiles.schemas import ProfileSchema
from resumes.models import Resume
from utils.notification import send_notification
from vacancies.entities import VacancyEntity
from vacancies.models import Apply, Keyword, Vacancy

from .entities import TeamEntity
from .models import Team, Token
from .schemas import (
    AnalyticsSchema,
    ApplySchema,
    EmailSchema,
    TeamCreateSchema,
    TeamSchema,
    TeamUpdateSchema,
    UsersSuggestionForVacancySchema,
    VacancySchema,
    VacancySuggestionForUserSchema,
)

team_router = Router()


@team_router.post(path="/create", response={201: TeamSchema, ERROR_CODES: ErrorSchema})
async def create_team(
    request: APIRequest, hackathon_id: uuid.UUID, create_schema: TeamCreateSchema
) -> tuple[int, TeamEntity]:
    user = request.user
    hackathon = await aget_object_or_404(Hackathon, id=hackathon_id)
    team = await Team.objects.acreate(
        hackathon=hackathon, name=create_schema.name, creator=user
    )
    await team.team_members.aadd(user)

    for vacancy_schema in create_schema.vacancies:
        vacancy = await Vacancy.objects.acreate(team=team, name=vacancy_schema.name)
        for kw in vacancy_schema.keywords:
            await Keyword.objects.acreate(vacancy=vacancy, text=kw)

    return 201, await team.to_entity()


@team_router.post(
    path="/accept_application", response={200: StatusSchema, ERROR_CODES: ErrorSchema}
)
async def accept_application(request: APIRequest, app_id: uuid.UUID):
    application = await aget_object_or_404(Apply, id=app_id)
    team = await Team.objects.aget(application=application)

    if await team.team_members.acontains(application.who_responsed):
        return 400, ErrorSchema(detail="User already in this team")

    total_team_participants = await team.team_members.acount()
    hackathon = await Hackathon.objects.aget(teams=team)

    if total_team_participants >= hackathon.max_participants:
        return 400, ErrorSchema(detail="Team is full")

    await application.adelete()
    await team.team_members.aadd(application.who_responsed)

    return 200, StatusSchema()


@team_router.post(
    path="/decline_application", response={200: StatusSchema, ERROR_CODES: ErrorSchema}
)
async def decline_application(request: APIRequest, app_id: uuid.UUID):
    application = await aget_object_or_404(Apply, id=app_id)
    await application.adelete()

    return 200, StatusSchema()


@team_router.post(
    path="/{team_id}/add_user",
    response={201: StatusSchema, ERROR_CODES: ErrorSchema},
)
async def add_user_to_team(
    request: APIRequest, team_id: uuid.UUID, email_schema: EmailSchema
):
    user = request.user

    team = await aget_object_or_404(Team.objects.select_related("creator"), id=team_id)
    if team.creator != user:
        return 403, ErrorSchema(
            detail="You are not creator and you can not edit this hackathon"
        )

    user_to_add = await aget_object_or_404(Account, email=email_schema.email)

    if user_to_add == user:
        return 400, ErrorSchema(detail="You can not add self")

    if await team.team_members.acontains(user_to_add):
        return 400, ErrorSchema(detail="User already in team")

    encoded_jwt = jwt.encode(
        {
            "createdAt": datetime.now().timestamp(),
            "id": team.id,
            "hackathon_id": team.hackathon.id,
            "email": user_to_add.email,
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    await Token.objects.acreate(token=encoded_jwt, is_active=True)

    await send_notification(
        users=user_to_add,
        context={
            "team": team,
            "invite_code": encoded_jwt,
            "frontend_url": FRONTEND_URL,
        },
        mail_template="teams/mail/invitation_to_team.html",
        telegram_template="teams/telegram/invitation_to_team.html",
    )

    return 201, StatusSchema()


@team_router.delete(
    path="/{team_id}/remove_user",
    response={200: TeamSchema, ERROR_CODES: ErrorSchema},
)
async def remove_user_from_team(
    request: APIRequest, team_id: uuid.UUID, email_schema: EmailSchema
):
    team = await aget_object_or_404(
        Team.objects.prefetch_related("team_members"), id=team_id
    )
    user_to_remove = await aget_object_or_404(
        team.team_members, user__email=email_schema.email
    )

    if team.creator != request.user:
        return 403, ErrorSchema(
            detail="You are not creator and you can not edit this team"
        )

    if user_to_remove == request.user:
        return 400, ErrorSchema(detail="You can not remove self")

    await team.team_members.aremove(user_to_remove)

    await send_notification(
        users=user_to_remove,
        context={"team": team},
        mail_template="teams/mail/user_kicked.html",
        telegram_template="teams/telegram/user_kicked.html",
    )

    return 200, await team.to_entity()


@team_router.post(
    path="/join-team",
    response={200: StatusSchema, ERROR_CODES: ErrorSchema},
)
async def join_team(request: APIRequest, team_id: uuid.UUID, token: str):
    user = request.user

    team = await aget_object_or_404(Team, id=team_id)

    tkn = await aget_object_or_404(Token, token=token)
    if not tkn.is_active:
        return 403, {"details": "token in not active"}

    tkn.is_active = False
    await tkn.asave()

    if await team.team_members.acontains(user):
        return 400, ErrorSchema(detail="User already in this team")

    total_team_participants = await team.team_members.acount()
    hackathon = await Hackathon.objects.aget(teams=team)

    if total_team_participants >= hackathon.max_participants:
        return 400, ErrorSchema(detail="Team is full")

    await team.team_members.aadd(user)

    return 200, StatusSchema()


@team_router.post(
    path="/leave-team", response={200: StatusSchema, ERROR_CODES: ErrorSchema}
)
async def leave_team(request: APIRequest, team_id: uuid.UUID):
    team = await aget_object_or_404(Team.objects.select_related("creator"), id=team_id)
    if not await team.team_members.acontains(request.user):
        return 400, ErrorSchema(detail="you are not member of this team")

    await team.team_members.aremove(request.user)

    if await team.team_members.acount() == 0:
        await team.adelete()
        return 200, StatusSchema()

    if team.creator == request.user:
        team.creator = await team.team_members.afirst()
        await team.asave()

        await send_notification(
            users=team.creator,
            context={"team": team},
            mail_template="teams/mail/new_team_owner.html",
            telegram_template="teams/telegram/new_team_owner.html",
        )
    else:
        await send_notification(
            users=team.creator,
            context={"who_left": request.user, "team": team},
            mail_template="teams/mail/user_left_team.html",
            telegram_template="teams/telegram/user_left_team.html",
        )

    return 200, StatusSchema()


@team_router.patch(
    path="/edit_team",
    response={200: TeamSchema, ERROR_CODES: ErrorSchema},
)
async def edit_team(
    request: APIRequest, id: uuid.UUID, update_schema: TeamUpdateSchema
):
    team = await aget_object_or_404(
        Team.objects.prefetch_related("team_members"), id=id
    )
    if team.creator != request.user:
        return 403, ErrorSchema(
            detail="You are not creator and you can not edit this team"
        )

    if update_schema.name is not None:
        team.name = update_schema.name
        await team.asave()

    if update_schema.vacancies is not None:
        await team.vacancies.adelete()
        for vacancy_schema in update_schema.vacancies:
            vacancy = await Vacancy.objects.acreate(name=vacancy_schema.name, team=team)

            for kw in vacancy_schema.keywords:
                await Keyword.objects.acreate(vacancy=vacancy, text=kw)

    return 200, await team.to_entity()


@team_router.get(path="/", response={200: list[TeamSchema], ERROR_CODES: ErrorSchema})
async def get_teams(
    request: APIRequest, hackathon_id: uuid.UUID
) -> tuple[int, list[Team]]:
    teams_query_set = Team.objects.filter(hackathon_id=hackathon_id).prefetch_related(
        "team_members"
    )
    teams = [await team.to_entity() async for team in teams_query_set]

    return 200, teams


@team_router.get(
    path="/team_vacancies",
    response={200: list[VacancySchema], ERROR_CODES: ErrorSchema},
)
async def get_team_vacancies(
    request: APIRequest, id: uuid.UUID
) -> tuple[int, list[VacancyEntity]]:
    team = await aget_object_or_404(Team.objects, id=id)
    vacancies = [await vacancy.to_entity() async for vacancy in team.vacancies.all()]

    return 200, vacancies


@team_router.get(
    path="/suggest_users_for_specific_vacansion/{vacansion_id}",
    response={200: UsersSuggestionForVacancySchema, ERROR_CODES: ErrorSchema},
)
async def get_suggest_users_for_specific_vacancy(
    request: APIRequest, vacansion_id: uuid.UUID
):
    vacancy = await aget_object_or_404(Vacancy, id=vacansion_id)
    keywords = {keyword.text.lower() async for keyword in vacancy.keywords}
    hackathon = await Hackathon.objects.aget(team_id=vacancy.team_id)

    participants_without_team = hackathon.participants.exclude(
        team_members__hackathon=hackathon
    )
    matching = {}
    async for participant in participants_without_team:
        try:
            resume = await Resume.objects.aget(user=participant)
        except Resume.DoesNotExist:
            continue

        skills = set()
        async for skill in resume.soft_skills.all():
            skills.add(skill.tag_text.lower())
        async for skill in resume.hard_skills.all():
            skills.add(skill.tag_text.lower())

        matching[participant] = len(skills & keywords)

    rating = sorted(matching.items(), key=lambda item: item[1], reverse=True)
    return 200, UsersSuggestionForVacancySchema(
        users=[await user.to_entity() for user, rate in rating]
    )


@team_router.get(
    path="/suggest_vacansions_for_specific_user/{resume_id}",
    response={200: VacancySuggestionForUserSchema, ERROR_CODES: ErrorSchema},
)
async def get_suggest_vacancies_for_specific_user(
    request: APIRequest, resume_id: uuid.UUID
):
    resume = await aget_object_or_404(Resume, id=resume_id)
    teams = Team.objects.filter(hackathon=resume.hackathon)

    skills = set()
    async for soft in resume.soft_skills.all():
        skills.add(soft.tag_text.lower())
    async for hard in resume.hard_skills.all():
        skills.add(hard.tag_text.lower())

    matching = {}
    async for team in teams:
        async for vacancy in team.vacancies.all():
            keywords = {
                keyword.text.lower() async for keyword in vacancy.keywords.all()
            }
            matching[vacancy] = len(keywords & skills)

    rating = sorted(matching.items(), key=lambda item: item[1], reverse=True)

    return 200, VacancySuggestionForUserSchema(
        vacantions=[await vacancy.to_entity() for vacancy, rate in rating]
    )


@team_router.post(
    path="/apply_for_job", response={200: StatusSchema, ERROR_CODES: ErrorSchema}
)
async def apply_for_job(request: APIRequest, vac_id: uuid.UUID):
    user = request.user

    vacancy = await aget_object_or_404(Vacancy, id=vac_id)
    team = await Team.objects.aget(vacancies=vacancy)
    if await team.team_members.acontains(user):
        return 400, ErrorSchema(detail="You are already in this team")

    total_team_participants = await team.team_members.acount()
    hackathon = await Hackathon.objects.aget(teams=team)

    if total_team_participants >= hackathon.max_participants:
        return 400, ErrorSchema(
            detail="You cant join this team because it reached max participants"
        )

    await Apply.objects.acreate(vac=vacancy, team=vacancy.team, who_responsed=user)

    await send_notification(
        users=team.creator,
        context={"who_response": user, "team": team},
        mail_template="teams/mail/new_job_response.html",
        telegram_template="teams/telegram/new_job_response.html",
    )

    return 200, StatusSchema()


@team_router.get(
    path="/get_applies_for_team",
    response={200: list[ApplySchema], ERROR_CODES: ErrorSchema},
)
async def get_team_applies(request: APIRequest, team_id: uuid.UUID):
    team = await aget_object_or_404(Team, id=team_id)
    if team.creator_id != request.user.id:
        return 403, ErrorSchema(detail="You are not creator of this team")

    applies = [await apply.to_entity() async for apply in team.applies.all()]

    return 200, applies


@team_router.get(path="/{team_id}", response={200: TeamSchema})
async def get_team_by_id(
    request: APIRequest, team_id: uuid.UUID
) -> tuple[int, TeamEntity]:
    team = await aget_object_or_404(
        Team.objects.prefetch_related("team_members"), id=team_id
    )
    return 200, await team.to_entity()


@team_router.get(
    path="/analytic/{hackathon_id}",
    response={200: AnalyticsSchema, ERROR_CODES: ErrorSchema},
)
async def analytics(
    request: APIRequest, hackathon_id: uuid.UUID
) -> tuple[int, AnalyticsSchema | ErrorSchema]:
    hackathon = await aget_object_or_404(Hackathon, id=hackathon_id)
    if hackathon.creator_id != request.user.id:
        return 403, ErrorSchema(detail="You are not the creator")

    hackathon_participants_count = await hackathon.participants.acount()
    users_with_team_count = await Team.team_members.through.objects.filter(
        team__hackathon=hackathon
    ).acount()

    if not hackathon_participants_count:
        return 200, AnalyticsSchema(procent=100)

    procent = (users_with_team_count / hackathon_participants_count) * 100

    return 200, AnalyticsSchema(procent=procent)


@team_router.get(
    path="/hackathon_summary/{hackathon_id}",
    response={200: HackathonSummarySchema, ERROR_CODES: ErrorSchema},
)
async def hackathon_summary(request: APIRequest, hackathon_id: uuid.UUID):
    hackathon = await aget_object_or_404(Hackathon, id=hackathon_id)
    if hackathon.creator_id != request.user.id:
        return 403, ErrorSchema(detail="You are not the creator")

    # Общее количество команд
    total_teams = await Team.objects.filter(hackathon=hackathon).acount()

    # Количество команд с максимальным количеством участников (полные команды)
    full_teams = await (
        Team.objects.filter(hackathon=hackathon)
        .annotate(num_members=Count("team_members"))
        .filter(num_members=hackathon.max_participants)
        .acount()
    )

    # Процент полных команд
    percent_full_teams = (full_teams / total_teams) * 100 if total_teams > 0 else 0

    # Список людей без команд
    people_without_teams = hackathon.participants.exclude(
        team_members__hackathon=hackathon
    )

    # Количество людей в командах из тех, кто зарегистрировался
    people_in_teams = await (
        Team.objects.filter(hackathon=hackathon)
        .values_list("team_members", flat=True)
        .distinct()
        .acount()
    )

    # Количество приглашенных людей (по количеству emails в хакатоне)
    invited_people = await hackathon.emails.acount()

    # Количество людей, принявших приглашение (по количеству участников)
    accepted_invite = await hackathon.participants.acount()

    return HackathonSummarySchema(
        total_teams=total_teams,
        full_teams=full_teams,
        percent_full_teams=percent_full_teams,
        people_without_teams=[
            await user.to_entity() async for user in people_without_teams
        ],
        people_in_teams=people_in_teams,
        invited_people=invited_people,
        accepted_invite=accepted_invite,
    )


@team_router.get(
    path="/hackathon/{hackathon_id}/participants_without_team",
    response={200: list[ProfileSchema], ERROR_CODES: ErrorSchema},
)
async def get_participants_without_team(request: APIRequest, hackathon_id: uuid.UUID):
    # Получаем хакатон по id
    hackathon = await aget_object_or_404(Hackathon, id=hackathon_id)
    if hackathon.creator_id != request.user.id:
        return 403, ErrorSchema(detail="You are not the creator")

    # Вычисляем участников, которые не входят в команды
    participants_without_team = hackathon.participants.exclude(
        team_members__hackathon=hackathon
    )

    # Возвращаем список участников без команды с именем, ролью и id
    return 200, [
        await participant.to_entity() async for participant in participants_without_team
    ]


@team_router.get(
    path="/hackathon/{hackathon_id}/pending_invitations",
    response={200: list[str], ERROR_CODES: ErrorSchema},
)
async def pending_invitations(request: APIRequest, hackathon_id: uuid.UUID):
    # Получаем хакатон по id
    hackathon = await aget_object_or_404(Hackathon, id=hackathon_id)
    if hackathon.creator_id != request.user.id:
        return 403, ErrorSchema(detail="You are not the creator")

    pending_emails = hackathon.emails.exclude(
        email__in=hackathon.participants.values_list("email", flat=True)
    )

    return 200, [pending_email.email async for pending_email in pending_emails.all()]
