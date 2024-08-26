from django.db import IntegrityError
from django.test import TestCase
from ninja.testing import TestAsyncClient

from accounts.models import Account
from hackathons.models import Hackathon
from profiles.schemas import ProfileSchema
from resumes.api import router


class TestResumesAPI(TestCase):
    def setUp(self) -> None:
        self.api_client = TestAsyncClient(router)

        self.user = Account.objects.create_user(
            email="test@example.org",
            username="test",
            is_organizator=False,
            password="test",
        )
        self.hackathon = Hackathon.objects.create(
            creator=self.user,
            name="test",
            description="test",
            status=Hackathon.Status.STARTED,
        )

        self.create_resume_schema = {
            "bio": "test",
            "hackathon_id": str(self.hackathon.id),
            "tech": ["tech1", "tech2"],
            "soft": ["soft1", "soft2"],
            "github": "test_github",
            "hh": "test_hhru",
            "telegram": "tg",
            "personal_website": "test_website",
        }
        self.resume_schema = self.create_resume_schema | {
            "role": None,
            "user": ProfileSchema.from_orm(self.user).model_dump(mode="json"),
        }

    async def test_resume_create(self) -> None:
        response = await self.api_client.post(
            path="/create/custom", json=self.resume_schema, user=self.user
        )

        self.assertEqual(response.status_code, 201)
        response_data = response.json()

        del response_data["id"]
        self.assertEqual(response_data, self.resume_schema)

    async def test_resume_duplicate(self) -> None:
        await self.api_client.post(
            path="/create/custom", json=self.resume_schema, user=self.user
        )
        with self.assertRaises(IntegrityError):
            await self.api_client.post(
                path="/create/custom", json=self.resume_schema, user=self.user
            )

    async def test_resume_get(self) -> None:
        await self.api_client.post(
            path="/create/custom", json=self.resume_schema, user=self.user
        )
        response = await self.api_client.get(
            path=f"/get?user_id={self.user.id}&hackathon_id={self.hackathon.id}",
            user=self.user,
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        del response_data["id"]
        self.assertEqual(response_data, self.resume_schema)

    async def test_resume_edit(self) -> None:
        await self.api_client.post(
            path="/create/custom", json=self.resume_schema, user=self.user
        )

        new_resume = self.resume_schema.copy()
        new_resume["telegram"] = "updated"
        new_resume["tech"] = ["123"]
        new_resume["soft"] = ["123"]

        response = await self.api_client.patch(
            path="/edit", json=new_resume, user=self.user
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        del response_data["id"]
        self.assertEqual(response_data, new_resume)
