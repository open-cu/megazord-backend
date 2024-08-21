from dataclasses import dataclass

from accounts.entities import AccountEntity
from hackathons.entities import HackathonEntity


@dataclass
class TeamEntity:
    id: str
    hackathon: HackathonEntity
    name: str
    creator: AccountEntity
    team_members: list[AccountEntity]
