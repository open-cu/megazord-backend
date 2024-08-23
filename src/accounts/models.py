import uuid
from datetime import timedelta
from random import randint

from asgiref.sync import sync_to_async
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone

from accounts.entities import AccountEntity, EmailEntity
from megazord.settings import CONFIRMATION_CODE_TTL


class MyAccountManager(BaseUserManager):
    def create_user(
        self,
        email: str,
        username: str,
        is_organizator: bool,
        password: str | None = None,
        age: int | None = None,
        city: str | None = None,
        work_experience: int | None = None,
        is_active: bool = False,
    ) -> "Account":
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            is_organizator=is_organizator,
            is_active=is_active,
            age=age,
            city=city,
            work_experience=work_experience,
        )
        user.set_password(password)
        user.save()

        return user

    async def acreate_user(
        self,
        email: str,
        username: str,
        is_organizator: bool,
        password: str | None = None,
        age: int | None = None,
        city: str | None = None,
        work_experience: int | None = None,
        is_active: bool = False,
    ) -> "Account":
        return await sync_to_async(self.create_user)(
            email=email,
            username=username,
            is_organizator=is_organizator,
            password=password,
            age=age,
            city=city,
            work_experience=work_experience,
            is_active=is_active,
        )

    def create_superuser(
        self, email: str, username: str, password: str, is_organizator: bool = True
    ) -> "Account":
        user = self.create_user(
            email=email,
            password=password,
            username=username,
            is_organizator=is_organizator,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save()

        return user


class Account(AbstractBaseUser):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True
    )
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = models.CharField(max_length=30)
    age = models.IntegerField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, default="")
    work_experience = models.IntegerField(blank=True, null=True)
    is_organizator = models.BooleanField(blank=False)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    telegram_id = models.IntegerField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "is_organizator"]

    objects = MyAccountManager()

    def __str__(self):
        return str(self.email)

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    async def to_entity(self) -> AccountEntity:
        return AccountEntity(
            id=self.id,
            email=self.email,
            username=self.username,
            age=self.age,
            city=self.city,
            work_experience=self.work_experience,
            is_organizator=self.is_organizator,
            date_joined=self.date_joined,
            last_login=self.last_login,
            is_admin=self.is_admin,
            is_active=self.is_active,
            is_staff=self.is_staff,
            is_superuser=self.is_superuser,
            telegram_id=self.telegram_id,
        )


class Email(models.Model):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email

    async def to_entity(self) -> EmailEntity:
        return EmailEntity(email=self.email)


class ConfirmationCode(models.Model):
    user = models.OneToOneField(
        Account, on_delete=models.CASCADE, unique=True, related_name="confirmation_code"
    )
    code = models.IntegerField()
    expire_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        self._update_expire_at()
        super().save(*args, **kwargs)

    async def asave(self, *args, **kwargs):
        self._update_expire_at()
        await super().asave(*args, **kwargs)

    def _update_expire_at(self):
        self.expire_at = timezone.now() + timedelta(minutes=CONFIRMATION_CODE_TTL)

    @classmethod
    async def generate(cls, user: Account):
        code, _ = await ConfirmationCode.objects.aupdate_or_create(
            user=user,
            defaults={"code": randint(100_000, 999_999)},
        )

        return code

    @property
    def is_expired(self) -> bool:
        return self.expire_at < timezone.now()
