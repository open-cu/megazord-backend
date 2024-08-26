import uuid

from ninja import ModelSchema, Schema
from pydantic import Field

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
