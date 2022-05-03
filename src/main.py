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

class TelegramBot:
    def __init__(self):
        self.bot = telebot.TeleBot(os.environ['TELEGRAM_BOT_TOKEN'])
        self.id = "@comapny_mentions"

    def get_bot(self):
        return self.bot

    def get_id(self):
        return self.id



def ru_token(string):
    """russian tokenize based on nltk.word_tokenize. only russian letter remaind."""
    return [i for i in word_tokenize(string) if re.match(r'[\u0400-\u04ffа́]+$', i)]


class CompaniesForSearch:

    def __init__(self):
        self.companies = ["Лукойл", "Lukoil", "X5 Retail Group", "Магнит", "Magnit", "Magnet",
             "Норникель", "Nornickel", "Сургутнефтегаз", "Surgutneftegas",
             "Татнефть", "TATNEFT", "Yandex", "Яндекс", "Новатэк",
             "NOVATEK", "Evraz", "Газпром", "Gazprom ", "Apple", "Google",
             "Coca-Cola", "Microsoft", "Samsung", "Amazon", "McDonald's",
             "Facebook", "Nike", "IKEA", "Tesla"]

    def get_names(self):
        return self.companies


class YandexDiskWork:

    def __init__(self):
        self.yandex_token = os.environ['YANDEX_TOKEN']

    def upload_file(self, loadfile, savefile, replace=False):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {self.yandex_token}'}
        res = requests.get(f'{url}/upload?path={savefile}&overwrite={replace}', headers=headers).json()
        with open(loadfile, 'rb') as f:
            requests.put(res['href'], files={'file': f})


    def download_file(self, path, file_name):
        base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
        public_key = path
        final_url = base_url + urlencode(dict(public_key=public_key))
        response = requests.get(final_url)
        download_url = response.json()['href']

        download_response = requests.get(download_url)
        with open('./src/' + file_name, 'wb') as f:
            f.write(download_response.content)


class TextAnalyzing:

    def __init__(self):
        YandexDiskWork().download_file("https://disk.yandex.ru/d/UtfYbeYZ7FORQQ", "NLP.pkl")
        with open('./src/NLP.pkl', 'rb') as f:
            self.tfidf_transformer, self.clf = pickle.load(f)
        f.close()

    def nlp_analyze(self, text):
        """rating the text"""
        x_test_tfidf =  self.tfidf_transformer.transform([text.lower()])
        x_test = x_test_tfidf

        predicted = self.clf.predict(x_test)
        return predicted[0]


class TextProcess:

    def __init__(self, bot_info):
        self.bot_info = bot_info

    def articles_processing(self, pair):
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

        mark = TextAnalyzing().nlp_analyze(new_text)
        message = company + " was mentioned here\n" + url + "\n\n" + "Message is " + mark
        mutex.acquire()
        self.bot_info.get_bot().send_message(self.bot_info.get_id(), message)
        mutex.release()


class MeduzaParser:

    def __init__(self, bot_info):
        self.bot_info = bot_info

    def meduza_parsing(self):
        """finding links with articles"""
        new_links = set()

        url = 'https://meduza.io/'  # url страницы

        tries = 10
        for tr in range(tries):
            try:
                page = requests.get(url)
            except Exception:
                if tr == 10:
                    self.bot_info.get_bot().send_message(self.bot_info.get_id(), 'I did not manage to connect to Meduza')
                    sleep(100)
                    self.meduza_parsing()
                else:
                    sleep(2)
            else:
                break

        soup = BeautifulSoup(page.text, "html.parser")
        all_news = soup.findAll('a', class_='Link-root Link-isInBlockTitle')
        default_datetime = datetime.datetime(1111, 1, 1, 1, 1, 1)

        YandexDiskWork().download_file("https://disk.yandex.ru/d/HfPp5TkTT8azQA", "date_meduza.pkl")
        try:
            with open('./src/date_meduza.pkl', 'rb') as file:
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
                except Exception:
                    if tr == 10:
                        self.bot_info.get_bot().send_message(self.bot_info.get_id(),
                                                             'I did not manage to connect to ' + url)
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
            self.bot_info.get_bot().send_message(self.bot_info.get_id(), 'We have not found new articles.')
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
                except Exception:
                    if tr == 10:
                        self.bot_info.get_bot().send_message(self.bot_info.get_id(),
                                                        'I did not manage to connect to ' + url + " in text finding")
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

            names_of_companies = CompaniesForSearch().get_names()
            for company in  names_of_companies:
                pos_in_text = article.find(company)
                if pos_in_text != -1:
                    links_for_analyze.add((article, company, url))

        if len(links_for_analyze) == 0:
            self.bot_info.get_bot().send_message(self.bot_info.get_id(),
                                                 'We have not found any mentions.')

        with open('./src/date_meduza.pkl', 'wb') as file:
            pickle.dump(last_date_time_obj, file)
        file.close()
        YandexDiskWork().upload_file('./src/date_meduza.pkl', 'HSE_project/date_meduza.pkl', True)

        for pair in links_for_analyze:
            sleep(10)
            TextProcess(self.bot_info).articles_processing(pair)
        return


class RbcParser:
    def __init__(self, bot_info):
        self.bot_info = bot_info

    def rbc_parsing(self):
        """finding links with articles"""
        new_links = set()

        website_url = 'https://www.rbc.ru/business/'  # url страницы

        tries = 10
        for tr in range(tries):
            try:
                page = requests.get(website_url)
            except Exception:
                if tr == 10:
                    self.bot_info.get_bot().send_message(self.bot_info.get_id(), 'I did not manage to connect to rbc business')
                    sleep(100)
                    self.rbc_parsing()
                else:
                    sleep(2)
            else:
                break

        soup = BeautifulSoup(page.text, "html.parser")
        all_news = soup.findAll('a', class_='item__link')
        default_datetime = datetime.datetime(1111, 1, 1, 1, 1, 1)

        YandexDiskWork().download_file("https://disk.yandex.ru/d/ZJIZB49KqrqscQ", "date_rbc.pkl")
        try:
            with open('./src/date_rbc.pkl', 'rb') as file:
                last_date = pickle.load(file)
        except IOError:
            last_date = default_datetime
        except EOFError:
            last_date = default_datetime

        for news in all_news:
            flag = 0
            link = str()

            curr_str = str(news)
            k = curr_str.find("href=")
            k += 6
            while str(news)[k] != '"':
                link += str(news)[k]
                k += 1

            url = link
            tries = 10
            for tr in range(tries):
                try:
                    page = requests.get(url)
                except Exception:
                    if tr == 10:
                        self.bot_info.get_bot().send_message(self.bot_info.get_id(),
                                                             'I did not manage to connect to ' + url)
                        flag = 1
                    else:
                        sleep(2)
                else:
                    break

            if flag == 1:
                continue

            soup = BeautifulSoup(page.text, "html.parser")
            all_news = soup.findAll('span', class_='article__header__date')
            date = str(all_news).split()[2].strip("content=\"")
            date_string = str(dateparser.parse(date))
            date_time_obj = datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S+03:00')
            if last_date == default_datetime:
                new_links.add((date_time_obj, link))
            else:
                if date_time_obj > last_date:
                    new_links.add((date_time_obj, link))

        # gathered all the new_links to search for company names

        if len(new_links) == 0:
            self.bot_info.get_bot().send_message(self.bot_info.get_id(), 'We have not found new articles.')
            return

        ready_for_analyze = set()
        new_links = sorted(new_links)
        last_date_time_obj = default_datetime

        for element in new_links:
            flag = 0
            url = element[1]
            last_date_time_obj = element[0]
            tries = 10
            for tr in range(tries):
                try:
                    page = requests.get(url)
                except Exception:
                    if tr == 10:
                        self.bot_info.get_bot().send_message(self.bot_info.get_id(),
                                                             'I did not manage to connect to ' + url + ' in text finding')
                        flag = 1
                    else:
                        sleep(2)
                else:
                    break

            if flag == 1:
                continue

            soup = BeautifulSoup(page.text, "html.parser")

            article = str()
            article_text = soup.findAll('div', class_="article__text article__text_free")
            soup1 = BeautifulSoup(str(article_text), "html.parser")

            for text in soup1.findAll('p'):
                article += text.get_text()

            names_of_companies = CompaniesForSearch().get_names()
            for company in names_of_companies:
                pos_in_text = article.find(company)
                if pos_in_text != -1:
                    ready_for_analyze.add((article, company, url))

        with open('./src/date_rbc.pkl', 'wb') as file:
            pickle.dump(last_date_time_obj, file)
        file.close()
        YandexDiskWork().upload_file('./src/date_rbc.pkl', 'HSE_project/date_rbc.pkl', True)

        if len(ready_for_analyze) == 0:
            self.bot_info.get_bot().send_message(self.bot_info.get_id(), 'We have not found any mentions.')
            return

        for pair in ready_for_analyze:
            sleep(10)
            TextProcess(self.bot_info).articles_processing(pair)
        return


bot_info = TelegramBot()
time_to_wait = 0.25 * 60 * 60
while 1:
    MeduzaParser(bot_info).meduza_parsing()
    RbcParser(bot_info).rbc_parsing()
    time.sleep(time_to_wait)