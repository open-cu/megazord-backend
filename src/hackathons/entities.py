from dataclasses import dataclass
from enum import StrEnum

from accounts.entities import AccountEntity, EmailEntity


class HackathonStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    STARTED = "STARTED"
    ENDED = "ENDED"


@dataclass
class HackathonEntity:
    id: str
    creator: AccountEntity
    name: str
    status: HackathonStatus
    image_cover: bytes
    description: str
    min_participants: int
    max_participants: int
    participants: list[AccountEntity]
    emails: list[EmailEntity]
    roles: list[str]
