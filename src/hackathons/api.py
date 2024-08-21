import logging
import uuid
from smtplib import SMTPException
from typing import Annotated, Any

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import aget_object_or_404
from ninja import File, Query, Router, UploadedFile

from accounts.models import Account, Email
from megazord.api.codes import ERROR_CODES
from megazord.api.requests import APIRequest
from megazord.schemas import ErrorSchema
from megazord.settings import FRONTEND_URL
from teams.models import Team
from teams.schemas import TeamSchema
from utils.mail import send_email_task
from utils.telegram import send_telegram_message

from .models import Hackathon, Role
from .schemas import (
    AddUserToHack,
    EditHackathon,
    EmailsSchema,
    Error,
    HackathonIn,
    HackathonSchema,
    StatusOK,
)
from .services import get_emails_from_csv, make_csv

logger = logging.getLogger(__name__)

hackathon_router = Router()
my_hackathon_router = Router()


@hackathon_router.post(
    path="/",
    response={201: HackathonSchema, 401: ErrorSchema, 400: ErrorSchema},
)
async def create_hackathon(
    request: APIRequest,
    body: HackathonIn,
    image_cover: UploadedFile = File(),
    csv_emails: UploadedFile = File(default=None),
):
    user = request.user
    if not user.is_organizator:
        return 403, {
            "detail": "You are not organizator and you can't create hackathons"
        }

    # Проверка на наличие запятых в названии хакатона
    if "," in body.name:
        return 400, {"detail": "Hackathon name cannot contain commas."}

    hackathon = Hackathon(
        creator=user,
        name=body.name,
        description=body.description,
        min_participants=body.min_participants,
        max_participants=body.max_participants,
        image_cover=image_cover.read(),
    )
    await hackathon.asave()

    for role in body.roles:
        await hackathon.roles.acreate(name=role)

    participants = set(body.participants)
    if csv_emails is not None:
        csv_participants = get_emails_from_csv(file=csv_emails)
        participants |= set(csv_participants)

    for participant in participants:
        # Создание или получение объекта Email
        email_obj, created = await Email.objects.aget_or_create(email=participant)

        # Добавление email в хакатон
        await hackathon.emails.aadd(email_obj)

    return 201, await hackathon.to_entity()


@hackathon_router.post(
    path="/join", response={200: HackathonSchema, ERROR_CODES: ErrorSchema}
)
async def join_hackathon(
    request: APIRequest,
    hackathon_id: uuid.UUID,
    role_name: Annotated[str | None, Query(alias="role")] = None,
):
    user = request.user
    hackathon = await aget_object_or_404(
        Hackathon, id=hackathon_id, status=Hackathon.Status.STARTED
    )
    if not await hackathon.emails.filter(email=user.email).aexists():
        return 403, ErrorSchema(
            detail="You have not been added to the hackathon participants"
        )

    if role_name is None:
        if await hackathon.roles.acount() != 0:
            return 400, ErrorSchema(detail="Please, choice role")
    else:
        role = await aget_object_or_404(Role, hackathon=hackathon, name=role_name)
        await role.users.aadd(user, through_defaults={"hackathon": hackathon})

    await hackathon.participants.aadd(user)
    return 200, await hackathon.to_entity()


@hackathon_router.post(
    path="/{hackathon_id}/send_invites",
    response={200: StatusOK, ERROR_CODES: ErrorSchema},
)
async def send_invites(
    request: APIRequest, hackathon_id: uuid.UUID, emails_schema: EmailsSchema
):
    hackathon = await aget_object_or_404(Hackathon, id=hackathon_id)

    if request.user != hackathon.creator:
        return 403, ErrorSchema(detail="You are not creator")

    try:
        send_email_task(
            template_name="hackathons/invitation_to_hackathon.html",
            context={"hackathon": hackathon},
            from_email="",
            recipient_list=emails_schema.emails,
        )
    except SMTPException as exc:
        logger.critical(exc)
        return 500, ErrorSchema(detail="Failed to send invites")

    return 200, StatusOK()


@hackathon_router.post(
    path="/{hackathon_id}/add_user",
    response={201: HackathonSchema, ERROR_CODES: Error},
)
async def add_user_to_hackathon(
    request: APIRequest, hackathon_id: uuid.UUID, email_schema: AddUserToHack
):
    me = request.user
    hackathon = await aget_object_or_404(Hackathon, id=hackathon_id)

    if hackathon.creator != me:
        return 403, {"details": "You are not creator and you can't edit this hackathon"}

    # Проверка, является ли email адресом создателя хакатона
    if hackathon.creator.email == email_schema.email:
        return 400, {"details": "user is creator of the hackathon"}
    try:
        # Поиск или создание записи email
        email_obj, created = await Email.objects.aget_or_create(
            email=email_schema.email
        )

        # Добавление email в хакатон
        await hackathon.emails.aadd(email_obj)
    except SMTPException as e:
        return 500, {"details": f"Failed to find user: {str(e)}"}

    return 201, await hackathon.to_entity()


@hackathon_router.delete(
    path="/{hackathon_id}/remove_user",
    response={201: HackathonSchema, 401: Error, 404: Error, 403: Error, 400: Error},
)
async def remove_user_from_hackathon(
    request: APIRequest, hackathon_id: uuid.UUID, email_schema: AddUserToHack
):
    me = request.user
    hackathon = await aget_object_or_404(Hackathon, id=hackathon_id)
    user_to_remove = await aget_object_or_404(Account, email=email_schema.email)
    if hackathon.creator == me:
        if user_to_remove != hackathon.creator:
            if user_to_remove in hackathon.participants.all():
                await hackathon.participants.aremove(user_to_remove)

                send_email_task(
                    template_name="hackathons/user_kicked.html",
                    context={"hackathon": hackathon},
                    from_email="",
                    recipient_list=[user_to_remove.email],
                )
            return 201, await hackathon.to_entity()
        else:
            return 400, {"detail": "This user is creator of hackathon"}
    else:
        return 403, {"detail": "You are not creator and you can't edit this hackathon"}


@hackathon_router.patch(
    path="/{id}",
    response={200: HackathonSchema, 401: Error, 400: Error, 403: Error, 404: Error},
)
async def edit_hackathons(request: APIRequest, id: uuid.UUID, body: EditHackathon):
    hackathon = await aget_object_or_404(Hackathon, id=id)
    user = request.user
    if hackathon.creator == user:
        if body.name:
            hackathon.name = body.name
        if body.description:
            hackathon.description = body.description
        if body.min_participants:
            hackathon.min_participants = body.min_participants
        if body.max_participants:
            hackathon.max_participants = body.max_participants
        await hackathon.asave()
        return 200, await hackathon.to_entity()
    else:
        return 403, {"detail": "You are not creator and you can't edit this hackathons"}


@hackathon_router.post(
    path="/{id}/change_photo",
    response={200: HackathonSchema, 401: Error, 400: Error, 403: Error, 404: Error},
)
async def change_photo(
    request: APIRequest, id: uuid.UUID, image_cover: UploadedFile = File(...)
):
    hackathon = await aget_object_or_404(Hackathon, id=id)
    user = request.user
    if hackathon.creator == user:
        hackathon.image_cover = image_cover.read()
        await hackathon.asave()
        return 200, await hackathon.to_entity()
    else:
        return 403, {"detail": "You are not creator and you can't edit this hackathons"}


@hackathon_router.get(
    path="/{id}",
    response={200: HackathonSchema, 401: Error, 400: Error, 404: Error},
)
async def get_specific_hackathon(
    request: APIRequest, id: uuid.UUID
) -> tuple[int, Hackathon]:
    hackathon = await aget_object_or_404(Hackathon, id=id)
    return 200, await hackathon.to_entity()


@my_hackathon_router.get(path="/", response={401: Error, 200: list[HackathonSchema]})
async def list_my_hackathons(request: APIRequest):
    user = request.user
    hackathons_queryset = Hackathon.objects.filter(
        Q(creator=user) | Q(participants=user)
    ).prefetch_related("creator")
    hackathons = [
        await hackathon.to_entity() async for hackathon in hackathons_queryset
    ]

    return 200, hackathons


@hackathon_router.get(
    path="/get_user_team/{id}", response={200: TeamSchema, ERROR_CODES: ErrorSchema}
)
async def get_user_team_in_hackathon(request: APIRequest, id: uuid.UUID):
    user = request.user
    hackathon = await aget_object_or_404(Hackathon, id=int(id))
    teams_queryset = Team.objects.filter(hackathon=hackathon).filter(team_members=user)
    teams = [await team.to_entity() async for team in teams_queryset]
    return teams


@hackathon_router.post(
    path="/{hackathon_id}/upload_emails",
    response={200: StatusOK, ERROR_CODES: ErrorSchema},
)
async def upload_emails_to_hackathon(
    request: APIRequest, hackathon_id: uuid.UUID, csv_file: UploadedFile = File(...)
):
    user = request.user
    hackathon = await aget_object_or_404(Hackathon, id=hackathon_id)

    # Проверка, является ли пользователь создателем хакатона
    if hackathon.creator != user:
        return 403, {
            "details": "You are not the creator and cannot edit this hackathon"
        }

    try:
        emails = get_emails_from_csv(file=csv_file)
        for email in emails:
            # Создание или получение объекта Email
            email_obj, created = await Email.objects.aget_or_create(email=email)

            # Добавление email в хакатон
            await hackathon.emails.aadd(email_obj)

        await hackathon.asave()

    except Exception as e:
        logger.critical(f"Failed to process CSV file: {str(e)}")
        return 400, {"details": "Failed to process CSV file"}

    return 200, {"details": "Emails successfully uploaded"}


@hackathon_router.get(
    path="/{hackathon_id}/export",
    response={200: Any, 404: Error, 403: Error},
)
async def export_participants_hackathon(request: APIRequest, hackathon_id: uuid.UUID):
    user = request.user
    hackathon = await aget_object_or_404(Hackathon, id=hackathon_id)
    user_in_participants = await hackathon.participants.filter(user=user).aexists()

    # Проверка, является ли пользователь создателем хакатона или его участником
    if hackathon.creator != user and not user_in_participants:
        return 403, {"details": "You do not have permission to access this hackathon"}

    csv_output = await make_csv(hackathon)
    # Создание HTTP-ответа с заголовками для загрузки файла
    response = HttpResponse(csv_output, content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="hackathon_{hackathon_id}_participants.csv"'
    )
    return response


@hackathon_router.post(
    path="/{hackathon_id}/start",
    response={200: StatusOK, ERROR_CODES: ErrorSchema},
)
async def start_hackathon(request: APIRequest, hackathon_id: uuid.UUID):
    hackathon = await aget_object_or_404(Hackathon, id=hackathon_id)
    if hackathon.creator != request.user:
        return 403, ErrorSchema(
            detail="You are not the creator or cannot edit this hackathon"
        )

    hackathon.status = Hackathon.Status.STARTED
    await hackathon.asave()

    try:
        send_email_task(
            template_name="hackathons/invitation_to_hackathon.html",
            context={"hackathon": hackathon, "frontend_url": FRONTEND_URL},
            from_email="",
            recipient_list=[email.email for email in hackathon.emails.all()],
        )
    except SMTPException as exc:
        logger.critical(exc)
        return 500, ErrorSchema(detail="Failed to send email")

    async for user in Account.objects.filter(email__in=hackathon.emails.all()):
        if user.telegram_id:
            telegram_message = (
                f"🎉 Приглашение в хакатон {hackathon.name}!\n"
                f"Для принятия участия, перейдите по ссылке: http://localhost:3000/join-hackathon?hackathon_id={hackathon.id}"
            )
            send_telegram_message(user.telegram_id, telegram_message)

    return 200, StatusOK()


@hackathon_router.post(
    path="/{hackathon_id}/end",
    response={200: StatusOK, ERROR_CODES: ErrorSchema},
)
async def end_hackathon(request: APIRequest, hackathon_id: uuid.UUID):
    hackathon = await aget_object_or_404(Hackathon, id=hackathon_id)
    if hackathon.creator != request.user:
        return 403, ErrorSchema(
            detail="You are not the creator or cannot edit this hackathon"
        )

    hackathon.status = Hackathon.Status.ENDED
    await hackathon.asave()

    async for user in hackathon.participants.all():
        if user.telegram_id:
            message_text = (
                f"🏁 Хакатон {hackathon.name} завершён!\n"
                f"Спасибо за участие! До встречи на следующих событиях."
            )
            send_telegram_message(user.telegram_id, message_text)


    return 200, StatusOK()
