from enum import StrEnum
from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from ninja import ModelSchema, Schema
from pydantic import EmailStr

from hackathons.models import Hackathon
from megazord.api.requests import APIRequest
from profiles.schemas import ProfileSchema


class HackathonStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    STARTED = "STARTED"
    ENDED = "ENDED"


class HackathonSchema(ModelSchema):
    participants: list[ProfileSchema]
    roles: list[str]
    role: str | None

    class Meta:
        model = Hackathon
        fields = [
            "id",
            "creator",
            "name",
            "status",
            "image_cover",
            "description",
            "min_participants",
            "max_participants",
        ]

    @staticmethod
    def resolve_roles(obj: Hackathon) -> list[str]:
        return [role.name for role in obj.roles.all()]

    @staticmethod
    def resolve_role(obj: Hackathon, context: dict[str, Any]) -> str | None:
        request: APIRequest = context["request"]

        try:
            role = obj.roles.get(users=request.user).name
        except ObjectDoesNotExist:
            role = None

        return role


class HackathonIn(Schema):
    name: str
    description: str
    min_participants: int = 1
    max_participants: int = 5
    participants: list[EmailStr] = []
    roles: list[str] = []


class EditHackathon(Schema):
    name: str | None = ""
    description: str | None = ""
    min_participants: int | None = None
    max_participants: int | None = None


class Error(Schema):
    details: str


class AddUserToHack(Schema):
    email: EmailStr


class EmailsSchema(Schema):
    emails: list[EmailStr]


class StatusOK(Schema):
    status: str = "ok"
