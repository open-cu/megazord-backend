from dataclasses import dataclass

from accounts.entities import AccountEntity
from hackathons.entities import HackathonEntity


@dataclass
class ResumeEntity:
    id: str
    user: AccountEntity
    hackathon: HackathonEntity

    role: str
    bio: str
    personal_website: str | None
    github: str | None
    hh: str | None
    telegram: str | None

    hard_skills: list[str]
    soft_skills: list[str]
