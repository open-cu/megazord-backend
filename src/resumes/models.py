import uuid

from django.db import models

from accounts.models import Account
from hackathons.models import Hackathon


class Resume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE)

    bio = models.TextField(blank=False)
    personal_website = models.CharField(max_length=200, blank=True)
    github = models.CharField(max_length=200, blank=True)
    hh = models.CharField(max_length=200, blank=True)
    telegram = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = (("user", "hackathon"),)


class HardSkillTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE, related_name="hard_skills"
    )
    tag_text = models.CharField(max_length=100, blank=False)


class SoftSkillTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE, related_name="soft_skills"
    )
    tag_text = models.CharField(max_length=200, blank=False)
