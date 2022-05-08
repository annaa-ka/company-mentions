"""Importing libraries"""

from MeduzaParserClass import MeduzaParser
from RbcParserClass import RbcParser
from TeleBotClass import TelegramBot
import time
import re
from threading import Lock
import nltk
from nltk import word_tokenize

nltk.download('punkt')
mutex = Lock()


# flake8: disable=E501


def ru_token(string):
    """russian tokenize based on nltk.word_tokenize. only russian letter remaind."""
    return [i for i in word_tokenize(string) if re.match(r'[\u0400-\u04ffа́]+$', i)]


bot_info = TelegramBot()
time_to_wait = 4 * 60 * 60
while 1:
    MeduzaParser(bot_info).meduza_parsing()
    RbcParser(bot_info).rbc_parsing()
    time.sleep(time_to_wait)
