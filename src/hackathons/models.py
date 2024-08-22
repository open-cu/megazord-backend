import uuid

from django.db import models

from accounts.models import Account, Email
from hackathons.entities import HackathonEntity, HackathonStatus


class Hackathon(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "NOT_STARTED"
        STARTED = "STARTED"
        ENDED = "ENDED"

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    creator = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="creator"
    )
    name = models.CharField(max_length=200, null=False)
    status = models.CharField(choices=Status, default=Status.NOT_STARTED)
    image_cover = models.BinaryField(null=False)
    description = models.TextField(null=False, default="описание хакатона")
    min_participants = models.IntegerField(null=True, default=3)
    max_participants = models.IntegerField(null=True, default=5)
    participants = models.ManyToManyField(Account, related_name="hackathons")
    emails = models.ManyToManyField(Email, related_name="hackathons")

    def __str__(self):
        return self.name

    async def to_entity(self) -> HackathonEntity:
        return HackathonEntity(
            id=self.id,
            creator=await self.creator.to_entity(),
            name=self.name,
            status=HackathonStatus(self.status),
            image_cover=self.image_cover,
            description=self.description,
            min_participants=self.min_participants,
            max_participants=self.max_participants,
            participants=[
                await participant.to_entity()
                async for participant in self.participants.all()
            ],
            emails=[await email.to_entity() async for email in self.emails.all()],
            roles=[role.name async for role in self.roles.all()],
        )


class Role(models.Model):
    hackathon = models.ForeignKey(
        Hackathon, on_delete=models.CASCADE, related_name="roles"
    )
    users = models.ManyToManyField(Account, through="UserRole")
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = (("hackathon", "name"),)


class UserRole(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("hackathon", "user"),)


class NotificationStatus(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    email = models.EmailField()
    hackathon = models.ForeignKey(
        Hackathon, on_delete=models.CASCADE, related_name="notification_statuses"
    )
    email_sent = models.BooleanField(default=False)
    telegram_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"NotificationStatus for {self.email} in hackathon {self.hackathon.name}"
