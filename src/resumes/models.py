import uuid

from django.db import models

from accounts.models import Account
from hackathons.models import Hackathon, Role
from resumes.entities import ResumeEntity


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

    async def to_entity(self) -> ResumeEntity:
        try:
            db_role = await Role.objects.aget(
                hackathon_id=self.hackathon_id, users_id=self.user_id
            )
            role = db_role.name
        except Role.DoesNotExist:
            role = None

        return ResumeEntity(
            id=self.id,
            user_id=str(self.user_id),
            hackathon_id=str(self.hackathon_id),
            role=role,
            bio=self.bio,
            personal_website=self.personal_website,
            github=self.github,
            hh=self.hh,
            telegram=self.telegram,
            hard_skills=[skill.tag_text async for skill in self.hard_skills.all()],
            soft_skills=[skill.tag_text async for skill in self.soft_skills.all()],
        )


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
