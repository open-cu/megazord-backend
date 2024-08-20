import uuid

from django.core.exceptions import ObjectDoesNotExist
from ninja import Field, ModelSchema, Schema

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


class ResumeSchema(ModelSchema):
    hackathon_id: uuid.UUID = Field(alias="hackathon.id")
    role: str | None
    tech: list[str] = []
    soft: list[str] = []

    @staticmethod
    def resolve_tech(obj: Resume) -> list[str]:
        return [skill.tag_text for skill in obj.hard_skills.all()]

    @staticmethod
    def resolve_soft(obj: Resume) -> list[str]:
        return [skill.tag_text for skill in obj.soft_skills.all()]

    @staticmethod
    def resolve_role(obj: Resume) -> str | None:
        try:
            role = obj.hackathon.roles.get(users=obj.user).name
        except ObjectDoesNotExist:
            role = None
        return role

    class Meta:
        model = Resume
        fields = ["id", "bio", "personal_website", "github", "hh", "telegram"]


class LinkSchema(Schema):
    link: str


class ResumeSuggestionSchema(Schema):
    bio: str | None = None
    hards: list[str] = []
    softs: list[str] = []
