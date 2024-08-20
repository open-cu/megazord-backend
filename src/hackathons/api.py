import logging
import random
import uuid
from datetime import datetime
from smtplib import SMTPException
from typing import Annotated, Any

import jwt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from mail_templated import send_mail
from ninja import File, Query, Router, UploadedFile

from accounts.models import Account, Email
from megazord.api.codes import ERROR_CODES
from megazord.api.requests import APIRequest
from megazord.schemas import ErrorSchema
from megazord.settings import SECRET_KEY
from teams.models import Team, Token
from teams.schemas import TeamById

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
def create_hackathon(
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
    )
    hackathon.save()
    hackathon.image_cover.save(image_cover.name, image_cover)

    for role in body.roles:
        hackathon.roles.create(name=role)

    participants = set(body.participants)
    if csv_emails is not None:
        csv_participants = get_emails_from_csv(file=csv_emails)
        participants |= set(csv_participants)

    for participant in participants:
        # Создание или получение объекта Email
        email_obj, created = Email.objects.get_or_create(email=participant)

        # Добавление email в хакатон
        hackathon.emails.add(email_obj)

    return 201, hackathon


@hackathon_router.post(
    path="/join", response={200: HackathonSchema, ERROR_CODES: ErrorSchema}
)
def join_hackathon(
    request: APIRequest,
    hackathon_id: uuid.UUID,
    role_name: Annotated[str | None, Query(alias="role")] = None,
):
    user = request.user
    hackathon = get_object_or_404(
        Hackathon, id=hackathon_id, status=Hackathon.Status.STARTED
    )
    if not hackathon.emails.filter(email=user.email).exists():
        return 403, ErrorSchema(
            detail="You have not been added to the hackathon participants"
        )

    if role_name is None:
        if hackathon.roles.count() != 0:
            return 400, ErrorSchema(detail="Please, choice role")
    else:
        role = get_object_or_404(Role, hackathon=hackathon, name=role_name)
        role.users.add(user, through_defaults={"hackathon": hackathon})

    hackathon.participants.add(user)
    return 200, hackathon


@hackathon_router.get(path="/", response={401: Error, 200: list[HackathonSchema]})
def list_hackathons(request):
    hackathons = Hackathon.objects.all()
    return 200, hackathons


@hackathon_router.post(
    path="/{hackathon_id}/send_invites",
    response={200: StatusOK, ERROR_CODES: ErrorSchema},
)
def send_invites(
    request: APIRequest, hackathon_id: uuid.UUID, emails_schema: EmailsSchema
):
    hackathon = get_object_or_404(Hackathon, id=hackathon_id)

    if request.user != hackathon.creator:
        return 403, ErrorSchema(detail="You are not creator")

    try:
        send_mail(
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
def add_user_to_hackathon(
    request: APIRequest, hackathon_id: uuid.UUID, email_schema: AddUserToHack
):
    me = request.user
    hackathon = get_object_or_404(Hackathon, id=hackathon_id)

    if hackathon.creator != me:
        return 403, {"details": "You are not creator and you can't edit this hackathon"}

    # Проверка, является ли email адресом создателя хакатона
    if hackathon.creator.email == email_schema.email:
        return 400, {"details": "user is creator of the hackathon"}
    try:
        # Поиск или создание записи email
        email_obj, created = Email.objects.get_or_create(email=email_schema.email)

        # Добавление email в хакатон
        hackathon.emails.add(email_obj)
        hackathon.save()
    except SMTPException as e:
        return 500, {"details": f"Failed to find user: {str(e)}"}

    return 201, hackathon


@hackathon_router.delete(
    path="/{hackathon_id}/remove_user",
    response={201: HackathonSchema, 401: Error, 404: Error, 403: Error, 400: Error},
)
def remove_user_from_hackathon(
    request: APIRequest, hackathon_id: uuid.UUID, email_schema: AddUserToHack
):
    me = request.user
    hackathon = get_object_or_404(Hackathon, id=hackathon_id)
    user_to_remove = get_object_or_404(Account, email=email_schema.email)
    if hackathon.creator == me:
        if user_to_remove != hackathon.creator:
            if user_to_remove in hackathon.participants.all():
                hackathon.participants.remove(user_to_remove)
                hackathon.save()
            return 201, hackathon
        else:
            return 400, {"detail": "This user is creator of hackathon"}
    else:
        return 403, {"detail": "You are not creator and you can't edit this hackathon"}


@hackathon_router.patch(
    path="/{id}",
    response={200: HackathonSchema, 401: Error, 400: Error, 403: Error, 404: Error},
)
def edit_hackathons(request: APIRequest, id: uuid.UUID, body: EditHackathon):
    hackathon = get_object_or_404(Hackathon, id=id)
    user = request.user
    if hackathon.creator == user:
        if body.name:
            hackathon.name = body.name
            hackathon.save()
        if body.description:
            hackathon.description = body.description
            hackathon.save()
        if body.min_participants:
            hackathon.min_participants = body.min_participants
            hackathon.save()
        if body.max_participants:
            hackathon.max_participants = body.max_participants
            hackathon.save()
        return 200, hackathon
    else:
        return 403, {"detail": "You are not creator and you can't edit this hackathons"}


@hackathon_router.post(
    path="/{id}/change_photo",
    response={200: HackathonSchema, 401: Error, 400: Error, 403: Error, 404: Error},
)
def change_photo(
    request: APIRequest, id: uuid.UUID, image_cover: UploadedFile = File(...)
):
    hackathon = get_object_or_404(Hackathon, id=id)
    user = request.user
    if hackathon.creator == user:
        if image_cover:
            hackathon.image_cover.save(image_cover.name, image_cover)
        return 200, hackathon
    else:
        return 403, {"detail": "You are not creator and you can't edit this hackathons"}


@hackathon_router.get(
    path="/{id}",
    response={200: HackathonSchema, 401: Error, 400: Error, 404: Error},
)
def get_specific_hackathon(request: APIRequest, id: uuid.UUID) -> tuple[int, Hackathon]:
    hackathon = get_object_or_404(Hackathon, id=id)
    return 200, hackathon


@my_hackathon_router.get(path="/", response={401: Error, 200: list[HackathonSchema]})
def list_myhackathons(request):
    user = request.user
    hackathons = Hackathon.objects.all()
    to_return = []
    for hack in hackathons:
        if hack.creator == user or user in hack.participants.all():
            to_return.append(hack)
    return 200, to_return


@hackathon_router.get(path="/get_user_team/{id}", response={200: TeamById, 404: Error})
def get_user_team_in_hackathon(request: APIRequest, id: uuid.UUID):
    user = request.user
    user_id = user.id
    hackathon = get_object_or_404(Hackathon, id=int(id))
    teams = Team.objects.filter(hackathon=hackathon).all()
    if teams:
        for t in teams:
            for member in t.team_members.all():
                if int(user_id) == int(member.id):
                    return 200, {
                        "id": t.id,
                        "hackathon": t.hackathon.id,
                        "name": t.name,
                        "creator": t.creator.id,
                        "team_members": [
                            {
                                "id": member.id,
                                "email": member.email,
                                "name": member.username,
                            }
                            for member in t.team_members.all()
                        ],
                    }
    else:
        return 404, {"details": "Not found"}


@hackathon_router.post(
    path="/{hackathon_id}/send_code",
    response={200: Any, 400: Error, 404: Error, 403: Error},
)
def send_code_to_email(request, hackathon_id: uuid.UUID, email_schema: AddUserToHack):
    # Получение хакатона по id
    hackathon = get_object_or_404(Hackathon, id=hackathon_id)

    # Проверка, существует ли email в списке emails хакатона
    email_obj = get_object_or_404(Email, email=email_schema.email)

    if email_obj not in hackathon.emails.all():
        return {"details": "Email not found in hackathon"}, 404

    # Генерация 6-значного кода
    confirmation_code = str(random.randint(100000, 999999))

    # Создание JWT для хранения кода подтверждения
    encoded_jwt = jwt.encode(
        {
            "confirmation_code": confirmation_code,
            "email": email_schema.email,
            "createdAt": datetime.utcnow().timestamp(),
        },
        SECRET_KEY,
        algorithm="HS256",
    )

    # Сохранение токена в базе данных
    try:
        Token.objects.create(token=encoded_jwt, is_active=True)
    except Exception as e:
        logger.critical(e)
        return {"details": "Failed to create token"}, 500

    # Отправка email с кодом подтверждения
    try:
        send_mail(
            template_name="hackathons/confirmation_code.html",
            context={"confirmation_code": encoded_jwt},
            from_email="",
            recipient_list=[email_schema.email],
        )
    except Exception as e:
        logger.critical(e)
        return {"details": "Failed to send email"}, 500

    return {"details": "Confirmation code sent successfully"}, 200


@hackathon_router.post(
    path="/{hackathon_id}/upload_emails",
    response={200: StatusOK, 400: Error, 404: Error, 403: Error},
)
def upload_emails_to_hackathon(
    request: APIRequest, hackathon_id: uuid.UUID, csv_file: UploadedFile = File(...)
):
    user = request.user
    hackathon = get_object_or_404(Hackathon, id=hackathon_id)

    # Проверка, является ли пользователь создателем хакатона
    if hackathon.creator != user:
        return 403, {
            "details": "You are not the creator and cannot edit this hackathon"
        }

    try:
        emails = get_emails_from_csv(file=csv_file)
        for email in emails:
            # Создание или получение объекта Email
            email_obj, created = Email.objects.get_or_create(email=email)

            # Добавление email в хакатон
            hackathon.emails.add(email_obj)

        hackathon.save()

    except Exception as e:
        logger.critical(f"Failed to process CSV file: {str(e)}")
        return 400, {"details": "Failed to process CSV file"}

    return 200, {"details": "Emails successfully uploaded"}


@hackathon_router.get(
    path="/{hackathon_id}/export",
    response={200: Any, 404: Error, 403: Error},
)
def export_participants_hackathon(request: APIRequest, hackathon_id: uuid.UUID):
    user = request.user
    hackathon = get_object_or_404(Hackathon, id=hackathon_id)

    # Проверка, является ли пользователь создателем хакатона или его участником
    if hackathon.creator != user and user not in hackathon.participants.all():
        return 403, {"details": "You do not have permission to access this hackathon"}

    csv_output = make_csv(hackathon)
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
def start_hackathon(request: APIRequest, hackathon_id: uuid.UUID):
    hackathon = get_object_or_404(Hackathon, id=hackathon_id)
    if hackathon.creator != request.user:
        return 403, ErrorSchema(
            detail="You are not the creator or cannot edit this hackathon"
        )

    hackathon.status = Hackathon.Status.STARTED
    hackathon.save()

    try:
        send_mail(
            template_name="hackathons/invitation_to_hackathon.html",
            context={"hackathon": hackathon},
            from_email="",
            recipient_list=[email.email for email in hackathon.emails.all()],
        )
    except SMTPException as exc:
        logger.critical(exc)
        return 500, ErrorSchema(detail="Failed to send email")

    # try:
    #     for email_obj in hackathon.emails.all():
    #         try:
    #             account = Account.objects.get(email=email_obj.email)
    #             if account.telegram_id:
    #                 telegram_message = (
    #                     f"🎉 Приглашение в хакатон {hackathon.name}!\n"
    #                     f"Для принятия участия, перейдите по ссылке: http://localhost:3000/join-hackathon?hackathon_id={hackathon.id}"
    #                 )
    #                 send_telegram_invitation(account.telegram_id, telegram_message)
    #         except Account.DoesNotExist:
    #             logger.warning(f"No account found for email: {email_obj.email}")
    # except Exception as e:
    #     logger.critical(f"Failed to send telegram message: {e}")
    #     return 500, ErrorSchema(detail="Failed to send telegram messages")

    return 200, StatusOK()


@hackathon_router.post(
    path="/{hackathon_id}/end",
    response={200: StatusOK, ERROR_CODES: ErrorSchema},
)
def end_hackathon(request: APIRequest, hackathon_id: uuid.UUID):
    hackathon = get_object_or_404(Hackathon, id=hackathon_id)
    if hackathon.creator != request.user:
        return 403, ErrorSchema(
            detail="You are not the creator or cannot edit this hackathon"
        )

    hackathon.status = Hackathon.Status.ENDED
    hackathon.save()

    return 200, StatusOK()
