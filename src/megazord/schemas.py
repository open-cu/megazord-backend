from ninja import Schema


class ErrorSchema(Schema):
    detail: str


class StatusSchema(Schema):
    status: str = "success"
