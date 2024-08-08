from django.contrib import auth
from django.http import Http404, HttpRequest
from ninja import Router

from auth import create_jwt, BadCredentials

from .models import Account
from .schemas import RegisterSchema, LoginSchema, TokenSchema, RegisterResponseSchema
from megazord.schemas import ErrorSchema

router = Router()


@router.post(
    path="/signup",
    summary="Register user",
    response={201: RegisterResponseSchema, 409: ErrorSchema, 422: ErrorSchema},
)
def signup(request: HttpRequest, schema: RegisterSchema) -> tuple[int, RegisterResponseSchema]:
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
    path="/signin", summary="Login user", response={200: TokenSchema, 404: ErrorSchema, 422: ErrorSchema}
)
def signin(request: HttpRequest, schema: LoginSchema) -> tuple[int, TokenSchema]:
    account = auth.authenticate(username=schema.email, password=schema.password)
    if account is None:
        raise BadCredentials()

    token = create_jwt(user_id=account.id)
    return 200, TokenSchema(token=token)


