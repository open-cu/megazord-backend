import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class MyAccountManager(BaseUserManager):
    def create_user(self, email, username, is_organizator, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")
        if is_organizator is None:
            raise ValueError("Users must have a is_organizator")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            is_organizator=is_organizator,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password, is_organizator):
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=username,
            is_organizator=is_organizator,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
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
    telegram_id = models.CharField(max_length=50, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "is_organizator"]

    objects = MyAccountManager()

    def __str__(self):
        return str(self.email)

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True


class Email(models.Model):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email
