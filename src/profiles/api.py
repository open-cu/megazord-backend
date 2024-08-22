import uuid

from django.shortcuts import aget_object_or_404
from ninja import Router

from accounts.entities import AccountEntity
from accounts.models import Account
from megazord.api.auth import AuthBearer
from megazord.api.requests import APIRequest
from megazord.schemas import ErrorSchema

from .schemas import ProfileEditSchema, ProfileSchema

router = Router(auth=AuthBearer())


@router.get(path="/profile", response={200: ProfileSchema, 401: ErrorSchema})
async def get_my_profile(request: APIRequest) -> AccountEntity:
    return await request.user.to_entity()


@router.patch(
    path="/profile",
    response={
        200: ProfileSchema,
        201: ProfileSchema,
        401: ErrorSchema,
        409: ErrorSchema,
    },
)
async def profile_patch(
    request: APIRequest, edit_schema: ProfileEditSchema
) -> AccountEntity:
    me = request.user
    me.age = edit_schema.age
    me.city = edit_schema.city
    me.username = edit_schema.username
    me.work_experience = edit_schema.work_experience
    await me.asave()

    return await me.to_entity()


@router.get(
    path="/profiles/{user_id}",
    response={200: ProfileSchema, 401: ErrorSchema, 404: ErrorSchema},
)
async def get_profile(request: APIRequest, user_id: uuid.UUID) -> AccountEntity:
    user = await aget_object_or_404(Account, id=user_id)

    return await user.to_entity()


@router.post(
    path="/link_telegram",
    summary="Link Telegram ID",
    response={200: dict, 404: ErrorSchema},
)
async def link_telegram(request: APIRequest, user_id: uuid.UUID, telegram_id: int):
    user = await aget_object_or_404(Account, id=user_id)

    user.telegram_id = telegram_id
    await user.asave()

    return {"detail": "Telegram ID привязан успешно"}


@router.get(
    path="/generate_telegram_link",
    summary="Generate Telegram Link",
    response={200: dict, 401: ErrorSchema},
)
async def generate_telegram_link(request: APIRequest) -> dict:
    user = request.user

    telegram_link = f"https://t.me/FindYourMate_bot?start={(user.id)}"

    return {"telegram_link": telegram_link}
