import requests
import telegram
import os
from pathlib import Path
from dotenv import load_dotenv
import time
import logging


BASE_DIR = Path(__file__).resolve().parent
DVMN_URL = 'https://dvmn.org'
DVMN_API_URL = 'https://dvmn.org/api/long_polling/'

RECONNECT_TIMEOUT = 20
API_TIMEOUT = 15


class BotLogHandler(logging.Handler):

    def __init__(self, bot, chat_id):
        super().__init__()
        self.bot = bot
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        self.bot.send_message(text=log_entry, chat_id=self.chat_id)


def fetch_attempt(api_url, headers, params, timeout):

    response = requests.get(
        api_url,
        headers=headers,
        params=params,
        timeout=timeout
        )
    response.raise_for_status()
    return response.json()


def main():

    load_dotenv(os.path.join(BASE_DIR, '.env'))
    DVMN_TOKEN = os.getenv('DVMN_TOKEN')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('CHAT_ID')
    dvmn_headers = {'Authorization': 'Token {}'.format(DVMN_TOKEN)}

    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    handler = BotLogHandler(bot, CHAT_ID)
    handler.setLevel(logging.DEBUG)
    log.addHandler(handler)

    log.info('Бот запущен')

    params = {}

    while True:
        try:
            attempt = fetch_attempt(
                DVMN_API_URL,
                dvmn_headers,
                params,
                API_TIMEOUT
                )
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            time.sleep(RECONNECT_TIMEOUT)
            continue
        except requests.exceptions.HTTPError as err:
            log.error(f'Возникла ошибка в работе бота: {str(err)}')
            time.sleep(RECONNECT_TIMEOUT)
            continue

        if attempt['status'] == 'found':
            params['timestamp'] = attempt['last_attempt_timestamp']

            last_attempt = attempt['new_attempts'][0]
            is_negative = last_attempt['is_negative']
            lesson_title = last_attempt['lesson_title']
            lesson_url = last_attempt['lesson_url']

            attempt_result = (
                "К сожалению, в работе нашлись ошибки." if is_negative
                else "Преподавателю все понравилось, \
                    можно приступать к следующему уроку."
                    )
            message = f"""\
                У вас проверили работу \
                    ["{lesson_title}".]({DVMN_URL}{lesson_url})
                {attempt_result}
                """

            bot.send_message(
                text=message,
                chat_id=CHAT_ID,
                parse_mode='Markdown'
            )

        else:
            params['timestamp'] = attempt['timestamp_to_request']


if __name__ == "__main__":
    main()
