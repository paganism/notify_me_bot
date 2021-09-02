import requests
import telegram
import os
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

DVMN_TOKEN = os.getenv('DVMN_TOKEN')
DVMN_URL = 'https://dvmn.org'
DVMN_API_URL = 'https://dvmn.org/api/long_polling/'
DVMN_HEADERS = {'Authorization': 'Token {}'.format(DVMN_TOKEN)}

timestamp = ''
params = {}
timeout = 15


def fetch_attempt(api_url, headers, params, timeout):
    try:
        response = requests.get(
            DVMN_API_URL,
            headers=DVMN_HEADERS,
            params=params,
            timeout=timeout
            )
        return response.json()
    except requests.exceptions.ReadTimeout:
        return
    except requests.exceptions.ConnectionError:
        return


if __name__ == "__main__":
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    counter = 1
    while True:

        attempt = fetch_attempt(DVMN_API_URL, DVMN_HEADERS, params, timeout)

        if not attempt:
            continue

        params['timestamp'] = attempt['last_attempt_timestamp']

        is_negative = attempt['new_attempts'][0]['is_negative']
        lesson_title = attempt['new_attempts'][0]['lesson_title']
        lesson_url = attempt['new_attempts'][0]['lesson_url']

        attempt_result = (
            "К сожалению, в работе нашлись ошибки."
            if is_negative else
            "Преподавателю всё понравилось, \
                можно приступать к следующему уроку!"
            )

        message = f'У вас проверили работу \
            ["{lesson_title}".]({DVMN_URL}{lesson_url})\
                \n\n{attempt_result}'

        bot.send_message(text=message, chat_id=CHAT_ID, parse_mode='Markdown')
