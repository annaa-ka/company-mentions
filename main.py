import schedule
import telebot
from time import sleep
import time
import pickle
from nltk.corpus import stopwords
import re
import requests
from bs4 import BeautifulSoup
from nltk import word_tokenize
from threading import Thread

def ru_token(string):
    """russian tokenize based on nltk.word_tokenize. only russian letter remaind."""
    return [i for i in word_tokenize(string) if re.match(r'[\u0400-\u04ffа́]+$', i)]

#bot section
with open(".env") as f:
    TOKEN = f.read().strip()

bot = telebot.TeleBot(TOKEN)
some_id = "@CompanyMentions"


old_links = set()
new_links = set()
links_for_analyze = set()
stopwords_set = set(stopwords.words('russian'))  # выгружаем ненужные слова
stopwords_set.update(["также", "это"])

companies = ["Лукойл", "Lukoil" "X5 Retail Group", "Магнит", "Magnit", "Magnet", "Норникель", "Nornickel",
             "Сургутнефтегаз", "Surgutneftegas", "Татнефть", "TATNEFT", "Yandex", "Яндекс", "Новатэк",
             "NOVATEK", "Evraz", "Газпром", "Gazprom " "Apple", "Google", "Coca-Cola", "Microsoft",
             "Samsung", "Amazon", "McDonald's", "Facebook", "NiKe", "IKEA", "Tesla"]


with open('NLP.pkl', 'rb') as f:
    tfidf_transformer, clf = pickle.load(f)

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
        bot.send_message(some_id, message)




def finding_links_for_searching_names():
    global old_links
    global new_links
    global companies
    global links_for_analyze

    url = 'https://meduza.io/'  # url страницы
    old_links = new_links.copy()

    tries = 10
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

    for i in range(len(all_news)):
        link = "meduza.io"
        curr_str = str(all_news[i])
        k = curr_str.find("href=")
        k += 6
        while str(all_news[i])[k] != '"':
            link += str(all_news[i])[k]
            k += 1
        new_links.add(link)
    diff = set(new_links - old_links)

    if len(diff) == 0:
        return bot.send_message(some_id, 'За сутки ничего не случилось!')

    print("hello1")

    # gathered all the new_links to serach for company names
    links_for_analyze = set()

    for link in diff:
        url = 'https://' + link   #подключаемся к сайту
        tries = 10
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

        for td in soup.find_all('ul', class_={"ListBlock-module_root__3Q3Ga  ListBlock-module_ul__2MRrS ListBlock-module_center__tdIwd"}):
            article += td.get_text()

        for company in companies:
            pos_in_text = article.find(company)
            if pos_in_text == -1:
                continue
            else:
                links_for_analyze.add((article, company, url))
    print("hello2")
    for pair in links_for_analyze:
        th = Thread(target=articles_processing, args=(pair, ))
        # print("works")
        th.start()

    # articles_processing(links_for_analyze)
    return


if __name__ == "__main__":
    # bot.send_message(some_id, "HI")
    finding_links_for_searching_names()
    #schedule.every().day.at("22:55").do(finding_links_for_searching_names)
    while True:
        schedule.run_pending()
        time.sleep(1)
