import uuid

from django.db import models

from accounts.models import Account, Email


class Hackathon(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "NOT_STARTED"
        STARTED = "STARTED"
        ENDED = "ENDED"

    # Используем UUID в качестве primary key
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    creator = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="creator"
    )
    name = models.CharField(max_length=200, null=False)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NOT_STARTED
    )
    image_cover = models.ImageField(upload_to="hackathon_images/", null=True)
    description = models.TextField(null=False, default="описание хакатона")
    min_participants = models.IntegerField(null=True, default=3)
    max_participants = models.IntegerField(null=True, default=5)
    participants = models.ManyToManyField(Account, related_name="participants")
    emails = models.ManyToManyField(Email, related_name="emails")

    @property
    def accepted_invite(self):
        return self.participants.count()

    def __str__(self):
        return self.name


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
