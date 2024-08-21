from celery import shared_task
from mail_templated import send_mail


@shared_task
def send_email_task(
    template_name: str, context: dict, from_email: str, recipient_list: list[str]
):
    send_mail(
        template_name=template_name,
        context=context,
        from_email=from_email,
        recipient_list=recipient_list,
    )
