"""Importing libraries"""
import time
from time import sleep
import re
import warnings
import pickle
import datetime
from threading import Lock
import schedule
import telebot
import nltk
import requests
from bs4 import BeautifulSoup
from nltk import word_tokenize
import dateparser


nltk.download('punkt')
mutex = Lock()


# flake8: disable=E501


def ru_token(string):
    """russian tokenize based on nltk.word_tokenize. only russian letter remaind."""
    return [i for i in word_tokenize(string) if re.match(r'[\u0400-\u04ffа́]+$', i)]


# bot section
with open(".env") as f:
    TOKEN = f.read().strip()
f.close()

bot = telebot.TeleBot(TOKEN)
SOME_ID = "@comapny_mentions"


COMPANIES = ["Лукойл", "Lukoil", "X5 Retail Group", "Магнит", "Magnit", "Magnet",
             "Норникель", "Nornickel", "Сургутнефтегаз", "Surgutneftegas",
             "Татнефть", "TATNEFT", "Yandex", "Яндекс", "Новатэк",
             "NOVATEK", "Evraz", "Газпром", "Gazprom ", "Apple", "Google",
             "Coca-Cola", "Microsoft", "Samsung", "Amazon", "McDonald's",
             "Facebook", "NiKe", "IKEA", "Tesla"]

warnings.filterwarnings(
    "ignore",
    message="The localize method is no longer necessary, "
            "as this time zone supports the fold attribute",
)

with open('NLP.pkl', 'rb') as f:
    tfidf_transformer, clf = pickle.load(f)
f.close()


def nlp_analyze(text):
    """rating the text"""
    x_test_tfidf = tfidf_transformer.transform([text.lower()])
    x_test = x_test_tfidf

    predicted = clf.predict(x_test)

    return predicted[0]


def articles_processing(pair):
    """processing article with getting essential sentences with mentions"""
    text, company, url = pair

    split_text = re.split('[?.!]', text)
    new_text = str()
    last_sentence = 0
    i = 0
    while i < (len(split_text)):
        if company in split_text[i]:
            if last_sentence == 0:
                if i - 2 >= 0:
                    new_text += split_text[i - 2] + '.'
                    new_text += split_text[i - 1] + '.'
                elif i - 1 >= 0:
                    new_text += split_text[i - 1] + '.'
                new_text += split_text[i]
                if i + 2 < len(split_text):
                    new_text += split_text[i + 1] + '.'
                    new_text += split_text[i + 2] + '.'
                elif i + 1 < len(split_text):
                    new_text += split_text[i + 1] + '.'
                last_sentence = i + 2
                i += 3
            else:
                if i - 2 > last_sentence:
                    new_text += split_text[i - 2] + '.'
                    new_text += split_text[i - 1] + '.'
                elif i - 1 > last_sentence:
                    new_text += split_text[i - 1] + '.'
                new_text += split_text[i] + '.'
                if i + 2 < len(split_text):
                    new_text += split_text[i + 1] + '.'
                    new_text += split_text[i + 2] + '.'
                elif i + 1 < len(split_text):
                    new_text += split_text[i + 1] + '.'
                last_sentence = i + 2
                i += 3
        else:
            i += 1

    mark = nlp_analyze(new_text)
    message = company + " was mentioned here\n" + url + "\n\n" + "Message is " + mark
    mutex.acquire()
    bot.send_message(SOME_ID, message)
    mutex.release()


def finding_links_for_searching_names():
    """finding links with articles"""

    new_links = set()

    url = 'https://meduza.io/'  # url страницы

    tries = 10000
    for _ in range(tries):
        try:
            page = requests.get(url)
        except KeyError as _:
            sleep(2)
            continue
        break
    else:
        sleep(3000)

    soup = BeautifulSoup(page.text, "html.parser")
    all_news = soup.findAll('a', class_='Link-root Link-isInBlockTitle')
    default_datetime = datetime.datetime(1111, 1, 1, 1, 1, 1)

    try:
        with open('date.pkl', 'rb') as file:
            last_date = pickle.load(file)
    except IOError:
        last_date = default_datetime
        # The file cannot be opened, or does not exist.
    except EOFError:
        last_date = default_datetime
        # The file is created, but empty so write new database to it.

    for news in all_news:
        link = "meduza.io"
        curr_str = str(news)
        k = curr_str.find("href=")
        k += 6
        while str(news)[k] != '"':
            link += str(news)[k]
            k += 1

        url = 'https://' + link  # подключаемся к сайту
        tries = 10000
        for _ in range(tries):
            try:
                page = requests.get(url)
            except KeyError as _:
                sleep(2)
                continue
            break
        else:
            sleep(3000)
        soup = BeautifulSoup(page.text, "html.parser")
        time_el = [x.text.strip() for x in soup.find_all('time')]
        first_elem = time_el[0]
        date_string = str(dateparser.parse(first_elem))
        date_time_obj = datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        if last_date == default_datetime:
            new_links.add((date_time_obj, link))
        else:
            if date_time_obj > last_date:
                new_links.add((date_time_obj, link))

    # gathered all the new_links to serach for company names
    if len(new_links) == 0:
        bot.send_message(SOME_ID, 'За сутки ничего не случилось!')
        return

    links_for_analyze = set()
    new_links = sorted(new_links)
    last_date_time_obj = default_datetime

    for element in new_links:
        link = element[1]
        last_date_time_obj = element[0]
        url = 'https://' + link  # подключаемся к сайту
        tries = 10000
        for _ in range(tries):
            try:
                page = requests.get(url)
            except KeyError as _:
                sleep(2)
                continue
            break
        else:
            sleep(3000)

        soup = BeautifulSoup(page.text, "html.parser")

        article = str()
        for blocks in soup.find_all('p', class_={'SimpleBlock-module_p__Q3azD',
                                                 "SimpleBlock-module_context_p__33saY ",
                                                 "SimpleBlock-module_lead__35nXx "
                                                 " SimpleBlock-module_center__2rjif"}):
            article += blocks.get_text()

        for blocks in soup.find_all('h3', class_={"SimpleBlock-module_h3__2Kv7Y  "
                                                  "SimpleBlock-module_center__2rjif"}):
            article += blocks.get_text()

        for blocks in soup.find_all('h4', class_={"SimpleBlock-module_h4__2TJO3  "
                                                  "SimpleBlock-module_center__2rjif"}):
            article += blocks.get_text()

        for blocks in soup.find_all('div', class_={"QuoteBlock-module_root__2GrcC"}):
            article += blocks.get_text()

        for blocks in soup.find_all('ul',
                                    class_={"ListBlock-module_root__3Q3Ga  "
                                            "ListBlock-module_ul__2MRrS "
                                            "ListBlock-module_center__blocksIwd"}):
            article += blocks.get_text()

        for company in COMPANIES:
            pos_in_text = article.find(company)
            if pos_in_text != -1:
                links_for_analyze.add((article, company, url))

    with open('date.pkl', 'wb') as file:
        pickle.dump(last_date_time_obj, file)
    file.close()

    for pair in links_for_analyze:
        articles_processing(pair)


schedule.every().day.at("18:59").do(finding_links_for_searching_names)
schedule.every().day.at("19:05").do(finding_links_for_searching_names)
schedule.every().day.at("19:11").do(finding_links_for_searching_names)
while True:
    schedule.run_pending()
    time.sleep(1)
