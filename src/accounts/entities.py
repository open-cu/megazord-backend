from dataclasses import dataclass
from datetime import datetime


@dataclass
class AccountEntity:
    id: str
    email: str
    username: str
    age: int | None
    city: str | None
    work_experience: int | None
    is_organizator: bool
    date_joined: datetime
    last_login: datetime
    is_admin: bool
    is_active: bool
    is_staff: bool
    is_superuser: bool
    telegram_id: str | None


@dataclass
class EmailEntity:
    email: str
