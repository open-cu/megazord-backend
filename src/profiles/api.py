from django.shortcuts import get_object_or_404
from ninja import Router

from accounts.models import Account
from auth import AuthBearer

from .schemas import ProfileSchema, ProfileEditSchema
from megazord.schemas import ErrorSchema

router = Router(auth=AuthBearer())


@router.get(
    path="/profile",
    response={200: ProfileSchema, 401: ErrorSchema}
)
def get_my_profile(request) -> tuple[int, Account]:
    return 200, request.auth


@router.patch(
    path="/profile",
    response={201: ProfileSchema, 401: ErrorSchema, 409: ErrorSchema}
)
def profile_patch(request, edit_schema: ProfileEditSchema) -> tuple[int, Account]:
    me: Account = request.auth
    me.age = edit_schema.age
    me.city = edit_schema.city
    me.username = edit_schema.username
    me.work_experience = edit_schema.work_experience
    me.save()

    return 201, me


@router.get(
    path="/profiles/{user_id}",
    response={200: ProfileSchema, 401: ErrorSchema, 404: ErrorSchema}
)
def get_profile(request, user_id: int) -> tuple[int, Account]:
    user = get_object_or_404(Account, id=user_id)

    return 200, user
