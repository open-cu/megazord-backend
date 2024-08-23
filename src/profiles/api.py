import uuid

from django.shortcuts import aget_object_or_404
from ninja import Router

from accounts.entities import AccountEntity
from accounts.models import Account
from megazord.api.auth import AuthBearer
from megazord.api.codes import ERROR_CODES
from megazord.api.requests import APIRequest
from megazord.schemas import ErrorSchema, StatusSchema
from megazord.settings import TELEGRAM_BOT_USERNAME

from .schemas import ProfileEditSchema, ProfileSchema, TelegramLinkSchema

router = Router(auth=AuthBearer())


@router.get(path="/profile", response={200: ProfileSchema, ERROR_CODES: ErrorSchema})
async def get_my_profile(request: APIRequest) -> tuple[int, AccountEntity]:
    return 200, await request.user.to_entity()


@router.patch(path="/profile", response={200: ProfileSchema, ERROR_CODES: ErrorSchema})
async def profile_patch(
    request: APIRequest, edit_schema: ProfileEditSchema
) -> tuple[int, AccountEntity]:
    me = request.user
    me.age = edit_schema.age
    me.city = edit_schema.city
    me.username = edit_schema.username
    me.work_experience = edit_schema.work_experience
    await me.asave()

    return 200, await me.to_entity()


@router.get(
    path="/profiles/{user_id}",
    response={200: ProfileSchema, ERROR_CODES: ErrorSchema},
)
async def get_profile(request: APIRequest, user_id: uuid.UUID) -> AccountEntity:
    user = await aget_object_or_404(Account, id=user_id)

    return await user.to_entity()


@router.post(
    path="/link_telegram",
    summary="Link Telegram ID",
    response={200: StatusSchema, ERROR_CODES: ErrorSchema},
)
async def link_telegram(request: APIRequest, user_id: uuid.UUID, telegram_id: int):
    user = await aget_object_or_404(Account, id=user_id)

    user.telegram_id = telegram_id
    await user.asave()

    return 200, StatusSchema()


@router.get(
    path="/generate_telegram_link",
    summary="Generate Telegram Link",
    response={200: TelegramLinkSchema, ERROR_CODES: ErrorSchema},
)
async def generate_telegram_link(request: APIRequest) -> tuple[int, TelegramLinkSchema]:
    user = request.user
    telegram_link = f"https://t.me/{TELEGRAM_BOT_USERNAME}?start={user.id}"

    return 200, TelegramLinkSchema(telegram_link=telegram_link)
