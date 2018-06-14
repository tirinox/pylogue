import os

TELEGRAM_BOT_TOKEN = ''  # insert your Telegram bot API token here

TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN or os.environ.get('BOT_API_KEY')
assert TELEGRAM_BOT_TOKEN, 'Please, provide API token'

