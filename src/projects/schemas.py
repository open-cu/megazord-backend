import uuid

from ninja import Field, Schema


class ProjectSchema(Schema):
    name: str = Field(max_length=200)
    resume_id: uuid.UUID
    description: str
