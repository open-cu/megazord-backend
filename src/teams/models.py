import logging
import uuid

from asgiref.sync import sync_to_async
from django.db import models

from accounts.models import Account
from hackathons.models import Hackathon
from teams.entities import TeamEntity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=200, blank=False)
    creator = models.ForeignKey(Account, on_delete=models.CASCADE)
    team_members = models.ManyToManyField(Account, related_name="team_members")

    async def to_entity(self) -> TeamEntity:
        creator = await sync_to_async(lambda: self.creator)()
        creator_entity = await creator.to_entity()
        logger.info(f"Creator entity: {creator_entity}")

        members_entities = [
            await member.to_entity()
            async for member in self.team_members.exclude(id=self.creator_id)
        ]
        logger.info(f"Members entities: {members_entities}")
        return TeamEntity(
            id=self.id,
            hackathon_id=str(self.hackathon_id),
            name=self.name,
            creator_id=str(self.creator_id),
            team_members=[creator_entity] + members_entities,
        )


class Token(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=2048)
    is_active = models.BooleanField()
