from datetime import timedelta, datetime, timezone

import jwt
from django.core.exceptions import ObjectDoesNotExist
from ninja.security import HttpBearer

from accounts.models import Account
from megazord.settings import SECRET_KEY
from .requests import APIRequest

JWT_ALGORITHM = "HS256"


class AuthException(Exception):
    pass


class InvalidToken(AuthException):
    pass


class BadCredentials(AuthException):
    pass


class AuthBearer(HttpBearer):
    def authenticate(self, request: APIRequest, token: str) -> str:
        try:
            jwt_data = validate_jwt(token=token)
        except jwt.InvalidTokenError:
            raise InvalidToken

        user_id = jwt_data.get("user_id")
        if not user_id:
            raise InvalidToken

        try:
            user = Account.objects.get(id=user_id)
        except ObjectDoesNotExist:
            raise InvalidToken

        request.user = user

        return token


def create_jwt(
        user_id: int,
        expires_delta: timedelta = timedelta(weeks=4)
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    jwt_data = {"user_id": user_id, "iat": datetime.now(timezone.utc).timestamp(), "exp": expire}
    token = jwt.encode(
        payload=jwt_data,
        key=SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    return token


def validate_jwt(token: str) -> dict:
    payload = jwt.decode(
        jwt=token,
        key=SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        options={
            "validate_exp": True,
            "validate_ait": True
        }
    )
    return payload