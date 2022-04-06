import time
import schedule
import telebot
from time import sleep
import re
import requests
from bs4 import BeautifulSoup
from nltk import word_tokenize
from threading import Thread, Lock
import warnings
import dateparser
import datetime
import pickle

mutex = Lock()

def ru_token(string):
    return [i for i in word_tokenize(string) if re.match(r'[\u0400-\u04ffа́]+$', i)]


# bot section
with open(".env") as f:
    TOKEN = f.read().strip()
f.close()

bot = telebot.TeleBot(TOKEN)
some_id = "@CompanyMentions"


companies = ["Лукойл", "Lukoil" "X5 Retail Group", "Магнит", "Magnit", "Magnet", "Норникель", "Nornickel",
             "Сургутнефтегаз", "Surgutneftegas", "Татнефть", "TATNEFT", "Yandex", "Яндекс", "Новатэк",
             "NOVATEK", "Evraz", "Газпром", "Gazprom " "Apple", "Google", "Coca-Cola", "Microsoft",
             "Samsung", "Amazon", "McDonald's", "Facebook", "NiKe", "IKEA", "Tesla"]

warnings.filterwarnings(
    "ignore",
    message="The localize method is no longer necessary, as this time zone supports the fold attribute",
)

with open('NLP.pkl', 'rb') as f:
    tfidf_transformer, clf = pickle.load(f)
f.close()


def NLP_analyze(text):
    X_test_tfidf = tfidf_transformer.transform([text.lower()])
    X_test = X_test_tfidf

    predicted = clf.predict(X_test)

    return predicted[0]


def articles_processing(pair):
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

    mark = NLP_analyze(new_text)
    message = company + " was mentioned here\n" + url + "\n\n" + "Message is " + mark
    mutex.acquire()
    bot.send_message(some_id, message)
    mutex.release()


def finding_links_for_searching_names():
    global companies
    new_links = set()

    url = 'https://meduza.io/'  # url страницы

    tries = 10000
    for attempt in range(tries):
        try:
            page = requests.get(url)
        except KeyError as e:
            sleep(2)
            continue
        break
    else:
        sleep(3000)

    soup = BeautifulSoup(page.text, "html.parser")
    all_news = soup.findAll('a', class_='Link-root Link-isInBlockTitle')
    default_datetime = datetime.datetime(1111, 1, 1, 1, 1, 1)

    try:
        with open('date.pkl', 'rb') as f:
            last_date = pickle.load(f)
    except IOError:
        last_date = default_datetime
        # The file cannot be opened, or does not exist.
    except EOFError:
        last_date = default_datetime
        # The file is created, but empty so write new database to it.

    for i in range(len(all_news)):
        print(i)
        link = "meduza.io"
        curr_str = str(all_news[i])
        k = curr_str.find("href=")
        k += 6
        while str(all_news[i])[k] != '"':
            link += str(all_news[i])[k]
            k += 1

        url = 'https://' + link  # подключаемся к сайту
        tries = 10000
        for attempt in range(tries):
            try:
                page = requests.get(url)
            except KeyError as e:
                sleep(2)
                continue
            break
        else:
            sleep(3000)
        soup = BeautifulSoup(page.text, "html.parser")
        t = [x.text.strip() for x in soup.find_all('time')]
        s = t[0]
        date_string = str(dateparser.parse(s))
        date_time_obj = datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        if last_date == default_datetime:
            new_links.add((date_time_obj, link))
        else:
            if date_time_obj <= last_date:
                continue
            else:
                new_links.add((date_time_obj, link))

    # gathered all the new_links to serach for company names
    print("Done")
    if len(new_links) == 0:
        print("Empty")
        bot.send_message(some_id, 'За сутки ничего не случилось!')
        return

    links_for_analyze = set()
    new_links = sorted(new_links)
    last_date_time_obj = default_datetime

    for element in new_links:
        link = element[1]
        last_date_time_obj = element[0]
        url = 'https://' + link  # подключаемся к сайту
        tries = 10000
        for attempt in range(tries):
            try:
                page = requests.get(url)
            except KeyError as e:
                sleep(2)
                continue
            break
        else:
            sleep(3000)

        soup = BeautifulSoup(page.text, "html.parser")

        article = str()
        for td in soup.find_all('p', class_={'SimpleBlock-module_p__Q3azD',
                                             "SimpleBlock-module_context_p__33saY ",
                                             "SimpleBlock-module_lead__35nXx  SimpleBlock-module_center__2rjif"}):
            article += td.get_text()

        for td in soup.find_all('h3', class_={"SimpleBlock-module_h3__2Kv7Y  SimpleBlock-module_center__2rjif"}):
            article += td.get_text()

        for td in soup.find_all('h4', class_={"SimpleBlock-module_h4__2TJO3  SimpleBlock-module_center__2rjif"}):
            article += td.get_text()

        for td in soup.find_all('div', class_={"QuoteBlock-module_root__2GrcC"}):
            article += td.get_text()

        for td in soup.find_all('ul', class_={
            "ListBlock-module_root__3Q3Ga  ListBlock-module_ul__2MRrS ListBlock-module_center__tdIwd"}):
            article += td.get_text()

        for company in companies:
            pos_in_text = article.find(company)
            if pos_in_text == -1:
                continue
            else:
                links_for_analyze.add((article, company, url))

    with open('date.pkl', 'wb') as file:
        pickle.dump(last_date_time_obj, file)
    file.close()

    for pair in links_for_analyze:
        th = Thread(target=articles_processing, args=(pair,))
        th.start()
    return


if __name__ == "__main__":
    finding_links_for_searching_names()
    # bot.send_message(some_id, 'З')
    schedule.every().day.at("16:32").do(finding_links_for_searching_names)
    while True:
        schedule.run_pending()
        time.sleep(1)