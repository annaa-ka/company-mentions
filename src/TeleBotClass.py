import os
import telebot


class TelegramBot:
    def __init__(self):
        self.bot = telebot.TeleBot(os.environ['TELEGRAM_BOT_TOKEN'])
        self.id = "@comapny_mentions"

    def get_bot(self):
        return self.bot

    def get_id(self):
        return self.id
