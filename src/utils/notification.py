import logging
from typing import Any, Sequence

from asgiref.sync import sync_to_async
from django.core.mail.backends.base import BaseEmailBackend
from django.db.models import QuerySet
from django.template.loader import render_to_string
from httpx import AsyncClient
from mail_templated import send_mail as send_mail_sync

from accounts.models import Account, Email
from megazord.settings import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

type Recipient[T] = Sequence[T] | QuerySet[T] | T


async def send_notification(
    users: Recipient[Account] | None = None,
    emails: Recipient[Email] | None = None,
    context: dict[str, Any] | None = None,
    mail_template: str | None = None,
    telegram_template: str | None = None,
):
    if users is None and emails is None:
        raise ValueError("Recipients have not been passed")

    if users is not None and emails is not None:
        raise ValueError("You can pass either `users` or `emails`")

    if context is None:
        context = {}

    if users:
        await send_notification_by_user(
            users=users,
            context=context,
            mail_template=mail_template,
            telegram_template=telegram_template,
        )

    if emails:
        await send_notification_by_email(
            emails=emails,
            context=context,
            mail_template=mail_template,
            telegram_template=telegram_template,
        )


async def send_notification_by_email(
    emails: Recipient[Email],
    context: dict[str, Any],
    mail_template: str | None = None,
    telegram_template: str | None = None,
):
    if isinstance(emails, QuerySet):
        emails = [email async for email in emails]
    elif isinstance(emails, Email):
        emails = [emails]

    for email in emails:
        try:
            user = Account.objects.get(email=email)
        except Account.DoesNotExist:
            user = None
        context.update({"current_user": user})

        if mail_template is not None:
            await send_email(
                template_name="", context=context, recipient_list=[email.email]
            )

        if (
            telegram_template is not None
            and user is not None
            and user.temail is not None
        ):
            await send_telegram_message(
                template_name=telegram_template,
                context=context,
                chat_id=user.telegram_id,
            )


async def send_notification_by_user(
    users: Recipient[Account],
    context: dict[str, Any],
    mail_template: str | None = None,
    telegram_template: str | None = None,
):
    if isinstance(users, QuerySet):
        users = [user async for user in users]
    elif isinstance(users, Account):
        users = [users]

    for user in users:
        context.update({"current_user": user})

        if mail_template is not None:
            await send_email(
                template_name="", context=context, recipient_list=[user.email]
            )

        if telegram_template is not None and user.telegram_id is not None:
            await send_telegram_message(
                template_name=telegram_template,
                context=context,
                chat_id=user.telegram_id,
            )


# @shared_task
async def send_email(
    template_name: str,
    context: dict[str, Any],
    recipient_list: list[str],
    from_email: str = "",
    fail_silently: bool = False,
    auth_user: str | None = None,
    auth_password: str | None = None,
    connection: BaseEmailBackend | None = None,
) -> None:
    logger.info(f"Sending email to `{recipient_list}`")

    await sync_to_async(send_mail_sync)(
        template_name=template_name,
        context=context,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=fail_silently,
        auth_user=auth_user,
        auth_password=auth_password,
        connection=connection,
    )


async def send_telegram_message(
    template_name: str, context: dict[str, Any], chat_id: int | Sequence[int]
) -> bool:
    logger.info(f"Sending telegram message to `{chat_id}`")

    message_text = render_to_string(template_name=template_name, context=context)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message_text, "parse_mode": "HTML"}

    async with AsyncClient() as client:
        response = await client.post(url=url, json=payload)
        if response.status_code != 200:
            logger.error(f"An error was occurred: {response.text}")
            return False

    return True
