from django.db import IntegrityError
from django.test import TestCase
from ninja.testing import TestClient

from accounts.models import Account
from hackathons.models import Hackathon
from resumes.api import router


# Create your tests here.

class TestResumesAPI(TestCase):
    def setUp(self) -> None:
        self.api_client = TestClient(router)

        self.user = Account.objects.create_user(
            email="test@example.org",
            username="test",
            is_organizator=False,
            password="test"
        )
        self.hackathon = Hackathon.objects.create(
            creator=self.user,
            name="test",
            description="test"
        )

        self.resume_schema = {
            "bio": "test",
            "hackathon_id": self.hackathon.id,
            "tech": ["tech1", "tech2"],
            "soft": ["soft1", "soft2"],
            "github": "test_github",
            "hh": "test_hhru",
            "telegram": "tg",
            "personal_website": "test_website"
        }

    def test_resume_create(self) -> None:
        response = self.api_client.post(
            path="/create/custom",
            json=self.resume_schema,
            user=self.user
        )

        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        del response_data["id"]
        self.assertEqual(response_data, self.resume_schema)

    def test_resume_duplicate(self) -> None:
        with self.assertRaises(IntegrityError):
            self.api_client.post(
                path="/create/custom",
                json=self.resume_schema,
                user=self.user
            )
            self.api_client.post(
                path="/create/custom",
                json=self.resume_schema,
                user=self.user
            )

    def test_resume_get(self) -> None:
        self.api_client.post(
            path="/create/custom",
            json=self.resume_schema,
            user=self.user
        )
        response = self.api_client.get(
            path=f"/get?user_id={self.user.id}&hackathon_id={self.hackathon.id}",
            user=self.user
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        del response_data["id"]
        self.assertEqual(response_data, self.resume_schema)

    def test_resume_edit(self) -> None:
        self.api_client.post(
            path="/create/custom",
            json=self.resume_schema,
            user=self.user
        )

        new_resume = self.resume_schema.copy()
        new_resume["telegram"] = "updated"
        new_resume["tech"] = ["123"]
        new_resume["soft"] = ["123"]

        response = self.api_client.patch(
            path="/edit",
            json=new_resume,
            user=self.user
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        del response_data["id"]
        self.assertEqual(response_data, new_resume)
