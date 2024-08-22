from dataclasses import dataclass

from accounts.entities import AccountEntity


@dataclass
class TeamEntity:
    id: str
    hackathon_id: str
    name: str
    creator_id: str
    team_members: list[AccountEntity]
