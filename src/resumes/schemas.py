import uuid
from typing import List
from uuid import UUID

from ninja import ModelSchema, Schema
from pydantic import BaseModel, Field

from profiles.schemas import ProfileSchema
from resumes.models import Resume


class ResumeCreateSchema(ModelSchema):
    hackathon_id: uuid.UUID
    tech: list[str]
    soft: list[str]

    class Meta:
        model = Resume
        fields = ["bio", "personal_website", "github", "hh", "telegram"]


class ResumeUpdateSchema(ResumeCreateSchema):
    class Meta:
        fields_optional = "__all__"


class ResumeSchema(Schema):
    id: uuid.UUID
    hackathon_id: uuid.UUID
    user: ProfileSchema
    bio: str
    personal_website: str | None
    github: str | None
    hh: str | None
    telegram: str | None

    role: str | None
    tech: list[str] = Field(alias="hard_skills")
    soft: list[str] = Field(alias="soft_skills")


class LinkSchema(Schema):
    link: str


class ResumeSuggestionSchema(Schema):
    bio: str | None = None
    hards: list[str] = []
    softs: list[str] = []


class TeamWithResumesSchema(BaseModel):
    id: UUID
    hackathon_id: UUID
    name: str
    creator_id: UUID
    resumes: List[ResumeSchema]
