from ninja import ModelSchema, Field, Schema

from resumes.models import Resume


class ResumeCreateSchema(ModelSchema):
    hackathon_id: int
    tech: list[str]
    soft: list[str]

    class Meta:
        model = Resume
        fields = ["bio", "personal_website", "github", "hh", "telegram"]


class ResumeUpdateSchema(ResumeCreateSchema):
    class Meta:
        fields_optional = "__all__"


class ResumeSchema(ModelSchema):
    hackathon_id: int = Field(alias="hackathon.id")
    tech: list[str] = []
    soft: list[str] = []

    @staticmethod
    def resolve_tech(obj: Resume) -> list[str]:
        return [skill.tag_text for skill in obj.hard_skills.all()]

    @staticmethod
    def resolve_soft(obj: Resume) -> list[str]:
        return [skill.tag_text for skill in obj.soft_skills.all()]

    class Meta:
        model = Resume
        fields = ["id", "bio", "personal_website", "github", "hh", "telegram"]


class LinkSchema(Schema):
    link: str


class ResumeSuggestionSchema(Schema):
    bio: str | None = None
    hards: list[str] = []
    softs: list[str] = []
