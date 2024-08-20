import uuid

from django.shortcuts import get_object_or_404
from ninja import Router

from accounts.models import Account
from megazord.api.auth import AuthBearer
from megazord.api.requests import APIRequest
from megazord.schemas import ErrorSchema

from .schemas import ProfileEditSchema, ProfileSchema

router = Router(auth=AuthBearer())


@router.get(path="/profile", response={200: ProfileSchema, 401: ErrorSchema})
def get_my_profile(request: APIRequest) -> Account:
    return request.user


@router.patch(
    path="/profile",
    response={
        200: ProfileSchema,
        201: ProfileSchema,
        401: ErrorSchema,
        409: ErrorSchema,
    },
)
def profile_patch(request: APIRequest, edit_schema: ProfileEditSchema) -> Account:
    me = request.user
    me.age = edit_schema.age
    me.city = edit_schema.city
    me.username = edit_schema.username
    me.work_experience = edit_schema.work_experience
    me.save()

    return me


@router.get(
    path="/profiles/{user_id}",
    response={200: ProfileSchema, 401: ErrorSchema, 404: ErrorSchema},
)
def get_profile(request: APIRequest, user_id: uuid.UUID) -> Account:
    user = get_object_or_404(Account, id=user_id)

    return user


@router.post(
    path="/link_telegram",
    summary="Link Telegram ID",
    response={200: dict, 404: ErrorSchema},
)
def link_telegram(request: APIRequest, user_id: uuid.UUID, telegram_id: str):
    user = get_object_or_404(Account, uuid=user_id)

    user.telegram_id = telegram_id
    user.save()

    return {"detail": "Telegram ID привязан успешно"}


@router.get(
    path="/generate_telegram_link",
    summary="Generate Telegram Link",
    response={200: dict, 401: ErrorSchema},
)
def generate_telegram_link(request: APIRequest) -> dict:
    user = request.user

    telegram_link = f"https://t.me/FindYourMate_bot?start={str(user.uuid)}"

    return {"telegram_link": telegram_link}
