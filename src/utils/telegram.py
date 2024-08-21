import logging

import httpx
from django.conf import settings
from ratelimit import limits


@limits(calls=30, period=1)
def send_telegram_message(chat_id, message_text):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {"chat_id": chat_id, "text": message_text}

    try:
        response = httpx.post(url, json=payload)

        if response.status_code == 200:
            return True
        else:
            logging.error(f"Ошибка при отправке сообщения: {response.text}")
            return False

    except httpx.RequestError as exc:
        logging.error(f"Произошла ошибка во время запроса {exc.request.url!r}: {exc}")
        return False
