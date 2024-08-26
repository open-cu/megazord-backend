from dataclasses import dataclass

from accounts.entities import AccountEntity


@dataclass
class ResumeEntity:
    id: str
    user: AccountEntity
    hackathon_id: str

    role: str
    bio: str
    personal_website: str | None
    github: str | None
    hh: str | None
    telegram: str | None

    hard_skills: list[str]
    soft_skills: list[str]
