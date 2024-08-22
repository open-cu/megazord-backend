import uuid

from ninja import Field, Schema
from pydantic import BaseModel

from profiles.schemas import ProfileSchema


class AnalyticsSchema(Schema):
    procent: float


class EmailSchema(Schema):
    email: str


class VacancyCreateSchema(BaseModel):
    name: str
    keywords: list[str]


class TeamCreateSchema(Schema):
    name: str
    vacancies: list[VacancyCreateSchema]


class TeamUpdateSchema(Schema):
    name: str | None = None
    vacancies: list[VacancyCreateSchema] | None = None


class TeamSchema(Schema):
    id: uuid.UUID
    hackathon: uuid.UUID = Field(alias="hackathon_id")
    name: str
    creator: uuid.UUID = Field(alias="creator_id")
    team_members: list[ProfileSchema]


class ApplySchema(Schema):
    app_id: uuid.UUID = Field(alias="id")
    team: uuid.UUID = Field(alias="team.id")
    vac: uuid.UUID = Field(alias="vacancy.id")
    who_responsed: uuid.UUID = Field(alias="who_responsed.id")


class VacancySchema(Schema):
    id: uuid.UUID
    name: str
    keywords: list[str]


class VacancySuggestionForUserSchema(Schema):
    vacantions: list[VacancySchema]


class UsersSuggestionForVacancySchema(Schema):
    class ProfileWithKeywords(ProfileSchema):
        keywords: list[str] = []

    users: list[ProfileWithKeywords]
