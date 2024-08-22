from django.contrib import auth
from django.shortcuts import aget_object_or_404
from ninja import Router
from ninja.errors import HttpError

from megazord.api.auth import BadCredentials, create_jwt
from megazord.api.codes import ERROR_CODES
from megazord.api.requests import APIRequest
from megazord.schemas import ErrorSchema, StatusSchema
from utils.notification import send_notification

from .entities import AccountEntity
from .models import Account, ConfirmationCode
from .schemas import (
    ActivationSchema,
    EmailSchema,
    LoginSchema,
    RegisterResponseSchema,
    RegisterSchema,
    TokenSchema,
)

router = Router()


@router.post(
    path="/signup",
    summary="Register user",
    response={201: RegisterResponseSchema, 409: ErrorSchema, 422: ErrorSchema},
)
async def signup(
    request: APIRequest, schema: RegisterSchema
) -> tuple[int, AccountEntity]:
    if "," in schema.username:
        raise HttpError(422, "Username cannot contain commas.")

    account = await Account.objects.create_user(
        email=schema.email,
        username=schema.username,
        password=schema.password,
        is_organizator=schema.is_organizator,
        age=schema.age,
        city=schema.city,
        work_experience=schema.work_experience,
    )
    confirmation_code = await ConfirmationCode.generate(user=account)

    await send_notification(
        users=account,
        context={"code": confirmation_code.code},
        mail_template="accounts/mail/account_confirmation.html",
    )

    return 201, await account.to_entity()


@router.post(path="/activate", response={200: StatusSchema, ERROR_CODES: ErrorSchema})
async def activate_account(
    request: APIRequest, activation_schema: ActivationSchema
) -> tuple[int, StatusSchema | ErrorSchema]:
    code = await aget_object_or_404(
        ConfirmationCode,
        user__email=activation_schema.email,
        code=activation_schema.code,
    )
    user = await Account.objects.aget(id=code.user_id)

    await code.adelete()
    if code.is_expired:
        return 400, ErrorSchema(detail="Code expired")

    user.is_active = True
    await user.asave()

    return 200, StatusSchema()


@router.post(
    path="/resend_code", response={200: StatusSchema, ERROR_CODES: ErrorSchema}
)
async def resend_code(
    request: APIRequest, email_schema: EmailSchema
) -> tuple[int, StatusSchema | ErrorSchema]:
    user = await aget_object_or_404(Account, email=email_schema.email)
    confirmation_code = await ConfirmationCode.objects.filter(user=user).afirst()
    if confirmation_code and not confirmation_code.is_expired:
        return 400, ErrorSchema(detail="Code has not expired yet")

    confirmation_code = await ConfirmationCode.generate(user=user)

    await send_notification(
        users=user,
        context={"code": confirmation_code.code},
        mail_template="accounts/mail/account_confirmation.html",
    )

    return 200, StatusSchema()


@router.post(
    path="/signin",
    summary="Login user",
    response={200: TokenSchema, 404: ErrorSchema, 422: ErrorSchema},
)
async def signin(request: APIRequest, schema: LoginSchema) -> tuple[int, TokenSchema]:
    account = await auth.aauthenticate(username=schema.email, password=schema.password)
    if account is None:
        raise BadCredentials()

    token = create_jwt(user_id=account.id)
    return 200, TokenSchema(token=token)
