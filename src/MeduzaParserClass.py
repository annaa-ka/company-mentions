from time import sleep
import pickle
import datetime
from threading import Thread
import requests
from bs4 import BeautifulSoup
import dateparser
from YandexDiskWorkClass import YandexDiskWork
from CompaniesForSearchClass import CompaniesForSearch
from TextWorkClasses import TextProcess


class MeduzaParser:

    def __init__(self, bot_info):
        self.bot_info = bot_info

    def meduza_parsing(self):
        """finding links with articles"""
        new_links = set()

        url = 'https://meduza.io/'  # url страницы
        self.bot_info.get_bot().send_message(self.bot_info.get_id(),
                                             'Start Meduza searching!')
        tries = 10
        for tr in range(tries):
            try:
                page = requests.get(url)
            except Exception:
                if tr == 10:
                    self.bot_info.get_bot().send_message(self.bot_info.get_id(),
                                                         'I did not manage to connect to Meduza')
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

        # self.bot_info.get_bot().send_message(self.bot_info.get_id(),
        #                                      'Links gathered')
        # gathered all the new_links to search for company names

        if len(new_links) == 0:
            self.bot_info.get_bot().send_message(self.bot_info.get_id(), 'We have not found new articles on Meduza.')
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
            for company in names_of_companies:
                pos_in_text = article.find(company)
                if pos_in_text != -1:
                    links_for_analyze.add((article, company, url))

        if len(links_for_analyze) == 0:
            self.bot_info.get_bot().send_message(self.bot_info.get_id(),
                                                 'We have not found any mentions on Meduza.')
            return

        with open('./src/date_meduza.pkl', 'wb') as file:
            pickle.dump(last_date_time_obj, file)
        file.close()
        YandexDiskWork().upload_file('./src/date_meduza.pkl', 'HSE_project/date_meduza.pkl', True)

        threads_arr = list()
        for pair in links_for_analyze:
            th = Thread(target=TextProcess(self.bot_info).articles_processing, args=(pair,))
            threads_arr.append(th)
            th.start()

        for th in threads_arr:
            th.join()
        return
