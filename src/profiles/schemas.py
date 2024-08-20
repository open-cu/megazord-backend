from ninja import ModelSchema

from accounts.models import Account


class ProfileSchema(ModelSchema):
    class Config:
        model = Account
        model_fields = [
            "id",
            "username",
            "email",
            "is_organizator",
            "age",
            "city",
            "work_experience",
        ]


class ProfileEditSchema(ModelSchema):
    class Config:
        model = Account
        model_fields = ["username", "age", "city", "work_experience"]
        model_fields_optional = ["username", "age", "city", "work_experience"]
