"""Importing libraries"""
import os
import time
from time import sleep
import re
import warnings
import pickle
import datetime
from threading import Lock
import telebot
import nltk
import requests
from bs4 import BeautifulSoup
from nltk import word_tokenize
from urllib.parse import urlencode
import dateparser

nltk.download('punkt')
mutex = Lock()


# flake8: disable=E501


def ru_token(string):
    """russian tokenize based on nltk.word_tokenize. only russian letter remaind."""
    return [i for i in word_tokenize(string) if re.match(r'[\u0400-\u04ffа́]+$', i)]


TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
YANDEX_TOKEN = os.environ['YANDEX_TOKEN']

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
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


def upload_file(loadfile, savefile, replace=False):
    URL = 'https://cloud-api.yandex.net/v1/disk/resources'
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {YANDEX_TOKEN}'}
    res = requests.get(f'{URL}/upload?path={savefile}&overwrite={replace}', headers=headers).json()
    with open(loadfile, 'rb') as f:
        try:
            requests.put(res['href'], files={'file':f})
        except KeyError:
           print("loh")


def download_file(path, file_name):
    base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
    public_key = path
    final_url = base_url + urlencode(dict(public_key=public_key))
    response = requests.get(final_url)
    download_url = response.json()['href']

    download_response = requests.get(download_url)
    with open('./src/' + file_name, 'wb') as f:
        f.write(download_response.content)


download_file("https://disk.yandex.ru/d/UtfYbeYZ7FORQQ", "NLP.pkl")
with open('./src/NLP.pkl', 'rb') as f:
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
    bot.send_message(SOME_ID, 'Start searching!')
    new_links = set()

    url = 'https://meduza.io/'  # url страницы

    tries = 10
    for tr in range(tries):
        try:
            page = requests.get(url)
        except Exception as exception:
            if tr == 10:
                bot.send_message(SOME_ID, 'I did not manage to connect to Meduza')
                sleep(100)
                finding_links_for_searching_names()
            else:
                sleep(2)
        else:
            break

    soup = BeautifulSoup(page.text, "html.parser")
    all_news = soup.findAll('a', class_='Link-root Link-isInBlockTitle')
    default_datetime = datetime.datetime(1111, 1, 1, 1, 1, 1)

    download_file("https://disk.yandex.ru/d/cwj_2bNX60GMzQ", "date.pkl")
    try:
        with open('./src/date.pkl', 'rb') as file:
            last_date = pickle.load(file)
    except IOError:
        last_date = default_datetime
    except EOFError:
        last_date = default_datetime

    for news in all_news:
        flag = 0

        link = "meduza.io"
        curr_str = str(news)
        k = curr_str.find("href=")
        k += 6
        while str(news)[k] != '"':
            link += str(news)[k]
            k += 1

        url = 'https://' + link
        tries = 10
        for tr in range(tries):
            try:
                page = requests.get(url)
            except Exception as exception:
                if tr == 10:
                    bot.send_message(SOME_ID, 'I did not manage to connect to ' + url)
                    flag = 1
                else:
                    sleep(2)
            else:
                break

        if flag == 1:
            continue

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

    # gathered all the new_links to search for company names

    if len(new_links) == 0:
        bot.send_message(SOME_ID, 'We have not found any mentions.')
        return

    links_for_analyze = set()
    new_links = sorted(new_links)
    last_date_time_obj = default_datetime

    for element in new_links:
        flag = 0
        link = element[1]
        last_date_time_obj = element[0]
        url = 'https://' + link
        tries = 10
        for tr in range(tries):
            try:
                page = requests.get(url)
            except Exception as exception:
                if tr == 10:
                    bot.send_message(SOME_ID, 'I did not manage to connect to ' + url + " in text finding")
                    flag = 1
                else:
                    sleep(2)
            else:
                break

        if flag == 1:
            continue

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

    if len(links_for_analyze) == 0:
        bot.send_message(SOME_ID, 'We have not found any mentions.')

    with open('./src/date.pkl', 'wb') as file:
        pickle.dump(last_date_time_obj, file)
    file.close()
    upload_file('./src/date.pkl', 'HSE_project/date.pkl', True)

    for pair in links_for_analyze:
        sleep(10)
        articles_processing(pair)
    return


time_to_wait = 0.25 * 60 * 60
while 1:
    finding_links_for_searching_names()
    time.sleep(time_to_wait)
