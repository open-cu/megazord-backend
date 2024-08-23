from django.db import IntegrityError
from django.test import TestCase
from ninja.testing import TestAsyncClient

from megazord.api.auth import BadCredentials

from .api import router
from .models import Account


class TestAccountsAPI(TestCase):
    def setUp(self) -> None:
        self.api_client = TestAsyncClient(router)

        self.user_schema = {
            "username": "test_user",
            "email": "test_user@corp.ru",
            "is_organizator": False,
            "age": 12,
            "city": "test_city",
            "work_experience": 12,
        }
        self.register_schema = self.user_schema | {"password": "test_password"}

    async def test_create_user(self) -> None:
        response = await self.api_client.post("/signup", json=self.register_schema)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), self.user_schema)

    async def test_create_user_conflict(self) -> None:
        with self.assertRaises(IntegrityError):
            await self.api_client.post("/signup", json=self.register_schema)
            await self.api_client.post("/signup", json=self.register_schema)

        # self.assertEqual(response.status_code, 409)

    async def test_login_user(self) -> None:
        await self.api_client.post("/signup", json=self.register_schema)

        # force activate user
        user = await Account.objects.aget(email=self.user_schema["email"])
        user.is_active = True
        await user.asave()

        login_data = {"email": "test_user@corp.ru", "password": "test_password"}
        response = await self.api_client.post("/signin", json=login_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.json())

    async def test_wrong_login_data_user(self) -> None:
        login_data = {"email": "test_user@corp.ru", "password": "test_password"}

        with self.assertRaises(BadCredentials):
            await self.api_client.post("/signin", json=login_data)
