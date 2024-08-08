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
    path="/profile", response={201: ProfileSchema, 401: ErrorSchema, 409: ErrorSchema}
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
def get_profile(request: APIRequest, user_id: int) -> Account:
    user = get_object_or_404(Account, id=user_id)

    return user
