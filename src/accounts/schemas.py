from ninja import Field, Schema


class RegisterResponseSchema(Schema):
    username: str
    email: str
    is_organizator: bool
    age: int | None
    city: str | None
    work_experience: int | None


class RegisterSchema(Schema):
    username: str = Field(min_length=1, max_length=30, required=True)
    email: str = Field(min_length=1, max_length=60, required=True)
    password: str = Field(min_length=6, required=True)
    is_organizator: bool
    age: int | None = None
    city: str | None = None
    work_experience: int | None = None


class LoginSchema(Schema):
    email: str = Field(min_length=1, max_length=60, required=True)
    password: str = Field(min_length=6, required=True)


class TokenSchema(Schema):
    token: str
