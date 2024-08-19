from django.contrib import auth
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError

from megazord.api.auth import BadCredentials, create_jwt
from megazord.api.requests import APIRequest
from megazord.schemas import ErrorSchema

from .models import Account
from .schemas import LoginSchema, RegisterResponseSchema, RegisterSchema, TokenSchema

router = Router()


@router.post(
    path="/signup",
    summary="Register user",
    response={201: RegisterResponseSchema, 409: ErrorSchema, 422: ErrorSchema},
)
def signup(
    request: APIRequest, schema: RegisterSchema
) -> tuple[int, RegisterResponseSchema]:
    if "," in schema.username:
        raise HttpError(422, "Username cannot contain commas.")

    account = Account.objects.create_user(
        email=schema.email,
        username=schema.username,
        password=schema.password,
        is_organizator=schema.is_organizator,
    )
    if schema.age is not None:
        account.age = schema.age
    if schema.city is not None:
        account.city = schema.city
    if schema.work_experience is not None:
        account.work_experience = schema.work_experience
    account.save()

    return 201, account


@router.post(
    path="/signin",
    summary="Login user",
    response={200: TokenSchema, 404: ErrorSchema, 422: ErrorSchema},
)
def signin(request: APIRequest, schema: LoginSchema) -> tuple[int, TokenSchema]:
    account = auth.authenticate(username=schema.email, password=schema.password)
    if account is None:
        raise BadCredentials()

    token = create_jwt(user_id=account.id)
    return 200, TokenSchema(token=token)


@router.post(
    path="/link_telegram",
    summary="Link Telegram ID",
    response={200: dict, 404: ErrorSchema},
)
def link_telegram(request: APIRequest, user_uuid: str, telegram_id: str):
    user = get_object_or_404(Account, uuid=user_uuid)

    user.telegram_id = telegram_id
    user.save()

    return {"detail": "Telegram ID привязан успешно"}


@router.get(
    path="/generate_telegram_link",
    summary="Generate Telegram Link",
    response={200: dict, 404: ErrorSchema},
)
def generate_telegram_link(request: APIRequest, email: str) -> dict:
    user = get_object_or_404(Account, email=email)

    telegram_link = f"https://t.me/FindYourMate_bot?start={str(user.uuid)}"

    return {"telegram_link": telegram_link}
