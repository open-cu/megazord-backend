from ninja import Field, Schema


class ProjectSchema(Schema):
    name: str = Field(max_length=200)
    resume_id: int
    description: str
