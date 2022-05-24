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
                    self.bot_info.get_bot().send_message(self.bot_info.get_id(),
                                                         'I did not manage to connect to rbc business')
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
            all_news = soup.findAll('time', class_='article__header__date')
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
            self.bot_info.get_bot().send_message(self.bot_info.get_id(), 'We have not found new articles on RBC.')
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
            self.bot_info.get_bot().send_message(self.bot_info.get_id(), 'We have not found any mentions on RBC.')
            return

        threads_arr = list()
        for pair in ready_for_analyze:
            th = Thread(target=TextProcess(self.bot_info).articles_processing, args=(pair,))
            threads_arr.append(th)
            th.start()

        for th in threads_arr:
            th.join()
        return
