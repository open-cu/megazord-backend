import uuid

from ninja import Field, Schema


class ProfileSchema(Schema):
    id: uuid.UUID
    username: str
    email: str
    is_organizator: bool
    age: int | None
    city: str | None
    work_experience: int | None


class ProfileEditSchema(Schema):
    username: str | None = Field(min_length=1, max_length=30, default=None)
    age: int | None = None
    city: str | None = None
    work_experience: int | None = None
