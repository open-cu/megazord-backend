import asyncio
import logging
from smtplib import SMTPException
from typing import Any, Sequence

from aiolimiter import AsyncLimiter
from asgiref.sync import sync_to_async
from django.core.mail.backends.base import BaseEmailBackend
from django.db.models import QuerySet
from django.template.loader import render_to_string
from httpx import AsyncClient
from mail_templated import send_mail as send_mail_sync

from accounts.models import Account, Email
from hackathons.models import NotificationStatus
from megazord.context import context_request
from megazord.settings import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

limiter = AsyncLimiter(max_rate=30, time_period=1.0)

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

    if mail_template is None and telegram_template is None:
        raise ValueError("Templates have not been passed")

    if users is not None and emails is not None:
        raise ValueError("You can pass either `users` or `emails`")

    if context is None:
        context = {}
    context.update(
        {
            "current_user": None,
            "frontend_url": context_request.get().META["HTTP_ORIGIN"],
        }
    )

    if users is not None:
        if isinstance(users, QuerySet):
            users = [user async for user in users]
        elif isinstance(users, Account):
            users = [users]

        await send_notification_by_user(
            users=users,
            context=context,
            mail_template=mail_template,
            telegram_template=telegram_template,
        )

    if emails is not None:
        if isinstance(emails, QuerySet):
            emails = [email async for email in emails]
        elif isinstance(emails, Email):
            emails = [emails]

        await send_notification_by_email(
            emails=emails,
            context=context,
            mail_template=mail_template,
            telegram_template=telegram_template,
        )


async def send_notification_by_email(
    emails: list[Email],
    context: dict[str, Any],
    mail_template: str | None = None,
    telegram_template: str | None = None,
):
    for email in emails:
        email_sent = True
        telegram_sent = True
        try:
            user = await Account.objects.aget(email=email)
            context["current_user"] = user
        except Account.DoesNotExist:
            user = None

        if mail_template is not None:
            email_sent = await send_email(
                template_name=mail_template,
                context=context,
                recipient_list=[email.email],
            )

        if (
            telegram_template is not None
            and user is not None
            and user.telegram_id is not None
        ):
            telegram_sent = await send_telegram_message(
                template_name=telegram_template,
                context=context,
                chat_id=user.telegram_id,
            )

        await process_notification_status(
            email=email.email, email_sent=email_sent, telegram_sent=telegram_sent
        )


async def send_notification_by_user(
    users: list[Account],
    context: dict[str, Any],
    mail_template: str | None = None,
    telegram_template: str | None = None,
):
    for user in users:
        context["current_user"] = user
        email_sent = True
        telegram_sent = True

        if mail_template is not None:
            email_sent = await send_email(
                template_name=mail_template,
                context=context,
                recipient_list=[user.email],
            )

        if telegram_template is not None and user.telegram_id is not None:
            telegram_sent = await send_telegram_message(
                template_name=telegram_template,
                context=context,
                chat_id=user.telegram_id,
            )

        await process_notification_status(
            email=user.email, email_sent=email_sent, telegram_sent=telegram_sent
        )


async def send_email(
    template_name: str,
    context: dict[str, Any],
    recipient_list: list[str],
    from_email: str = "",
    fail_silently: bool = False,
    auth_user: str | None = None,
    auth_password: str | None = None,
    connection: BaseEmailBackend | None = None,
) -> bool:
    logger.info(f"Sending email to `{recipient_list}`")

    try:
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
    except SMTPException as exc:
        logger.error(f"Failed sent email to `{recipient_list}`: {exc}")
        return False
    return True


async def send_telegram_message(
    template_name: str, context: dict[str, Any], chat_id: int
) -> bool:
    logger.info(f"Sending telegram message to `{chat_id}`")

    message_text = render_to_string(template_name=template_name, context=context)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message_text, "parse_mode": "HTML"}

    async with limiter:
        async with AsyncClient() as client:
            response = await client.post(url=url, json=payload)
            if response.status_code == 200:
                logger.info(f"Message sent successfully to `{chat_id}`")
                return True
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                logger.warning(
                    f"Too many requests. Retrying after {retry_after} seconds."
                )
                await asyncio.sleep(retry_after)
            else:
                logger.error(f"Failed sent telegram message to `{chat_id}")
                return False

    return True


async def process_notification_status(
    email: str, email_sent: bool, telegram_sent: bool
) -> None:
    await NotificationStatus.objects.filter(email=email).adelete()

    if not email_sent or not telegram_sent:
        await NotificationStatus.objects.acreate(
            email=email, email_sent=email_sent, telegram_sent=telegram_sent
        )
