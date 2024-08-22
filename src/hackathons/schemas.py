import base64
import uuid

from ninja import Schema
from pydantic import EmailStr

from hackathons.entities import HackathonEntity, HackathonStatus
from profiles.schemas import ProfileSchema


class HackathonSchema(Schema):
    id: uuid.UUID
    creator: ProfileSchema
    name: str
    status: HackathonStatus
    image_cover: str
    description: str
    min_participants: int
    max_participants: int
    participants: list[ProfileSchema]
    roles: list[str]

    @staticmethod
    def resolve_image_cover(obj: HackathonEntity) -> str:
        return base64.b64encode(obj.image_cover).decode()


class HackathonCreateSchema(Schema):
    name: str
    description: str
    min_participants: int = 1
    max_participants: int = 5
    participants: list[EmailStr] = []
    roles: list[str] = []


class HackathonEditSchema(Schema):
    name: str | None = ""
    description: str | None = ""
    min_participants: int | None = None
    max_participants: int | None = None


class HackathonSummarySchema(Schema):
    total_teams: int
    full_teams: int
    percent_full_teams: float
    people_without_teams: list[ProfileSchema]
    people_in_teams: int
    invited_people: int
    accepted_invite: int


class EmailSchema(Schema):
    email: EmailStr


class EmailsSchema(Schema):
    emails: list[EmailStr]
