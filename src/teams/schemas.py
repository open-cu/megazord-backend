import uuid

from ninja import Field, Schema
from pydantic import BaseModel, ConfigDict

from profiles.schemas import ProfileSchema


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
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    hackathon: uuid.UUID = Field(alias="hackathon_id")
    name: str
    creator: uuid.UUID = Field(alias="creator_id")
    team_members: list[ProfileSchema]


class ApplySchema(Schema):
    app_id: uuid.UUID = Field(alias="id")
    team: uuid.UUID = Field(alias="team_id")
    vac: uuid.UUID = Field(alias="vacancy_id")
    who_responsed: uuid.UUID = Field(alias="who_response_id")


class VacancySchema(Schema):
    id: uuid.UUID
    name: str
    keywords: list[str]
    team: TeamSchema


class VacancySuggestionForUserSchema(Schema):
    vacantions: list[VacancySchema]


class UsersSuggestionForVacancySchema(Schema):
    class ProfileWithKeywords(ProfileSchema):
        keywords: list[str] = []

    users: list[ProfileWithKeywords]
