# Generated by Django 5.1 on 2024-08-20 22:13

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vacancies", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="apply",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False
            ),
        ),
        migrations.AlterField(
            model_name="keyword",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False
            ),
        ),
        migrations.AlterField(
            model_name="vacancy",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False
            ),
        ),
    ]