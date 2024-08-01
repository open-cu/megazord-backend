from typing import List, Optional

from ninja import Schema

from profiles.schemas import ProfileSchema


class HackathonSchema(Schema):
    id: int
    creator_id: int
    name: str
    image_cover: str
    description: str
    min_participants: int | None
    max_participants: int | None
    participants: list[ProfileSchema]


class HackathonIn(Schema):
    name: str
    description: str
    min_participants: int
    max_participants: int
    participants: list[str]


class HackathonOut(Schema):
    creator: int
    name: str
    description: str
    participants: list[str]
    imave_cover: str
    min_participants: int
    max_participants: int


class EditHackathon(Schema):
    name: str | None = ""
    description: str | None = ""
    min_participants: int | None = None
    max_participants: int | None = None


class Error(Schema):
    details: str


class AddUserToHack(Schema):
    email: str


class StatusOK(Schema):
    status: str = "ok"
