import base64
import uuid
from enum import StrEnum
from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from ninja import Schema
from pydantic import EmailStr

from hackathons.models import Hackathon
from megazord.api.requests import APIRequest
from profiles.schemas import ProfileSchema


class HackathonStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    STARTED = "STARTED"
    ENDED = "ENDED"


class HackathonSchema(Schema):
    id: uuid.UUID
    creator_id: uuid.UUID
    name: str
    status: HackathonStatus
    image_cover: str
    description: str
    min_participants: int | None
    max_participants: int | None
    participants: list[ProfileSchema]
    roles: list[str]
    role: str | None

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

    @staticmethod
    def resolve_image_cover(obj: Hackathon) -> str:
        return base64.b64encode(obj.image_cover).decode()


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
