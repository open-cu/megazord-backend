from typing import Any

from django.http import HttpRequest

from accounts.models import Account


class APIRequest(HttpRequest):
    user: Account
    auth: Any
