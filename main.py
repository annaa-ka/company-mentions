import schedule
import telebot
from threading import Thread
from time import sleep

TOKEN = None

with open(".env") as f:
    TOKEN = f.read().strip()

bot = telebot.TeleBot(TOKEN)
some_id = "@CompanyMentions"


def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)

def function_to_run():
    return bot.send_message(some_id, "Hello world.")

if __name__ == "__main__":
    schedule.every().day.at("18:00").do(function_to_run)
    Thread(target=schedule_checker).start()
