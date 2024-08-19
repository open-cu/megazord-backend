# Generated by Django 5.1 on 2024-08-19 15:30

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_account_telegram_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
