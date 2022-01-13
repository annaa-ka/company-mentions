import schedule
import telebot
from threading import Thread
from time import sleep

import requests
from bs4 import BeautifulSoup


with open(".env") as f:
    TOKEN = f.read().strip()

bot = telebot.TeleBot(TOKEN)
some_id = "@CompanyMentions"

old_links = set()
new_links = set()
links_for_analyze = set()
companies = ["Лукойл", "Lukoil" "X5 Retail Group", "Магнит", "Magnit", "Magnet", "Норникель", "Nornickel",
             "Сургутнефтегаз", "Surgutneftegas", "Татнефть", "TATNEFT", "Yandex", "Яндекс", "Новатэк",
             "NOVATEK", "Evraz", "Газпром", "Gazprom " "Apple", "Google", "Coca-Cola", "Microsoft",
             "Samsung", "Amazon", "McDonald's", "Facebook", "NiKe", "IKEA", "Tesla"]


def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)


def finding_links_for_searching_names():
    global old_links
    global new_links
    global companies
    global links_for_analyze

    url = 'https://meduza.io/'  # url страницы
    old_links = new_links.copy()

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


    # gathered all the new_links to serach for company names
    links_for_analyze = set()

    for link in diff:
        url = 'https://' + link
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
        block_with_the_article = soup.findAll('div', class_='GeneralMaterial-article')
        for company in companies:
            text = str(block_with_the_article)
            p1 = text.find("<figcaption>")
            while p1 != -1:
                p2 = text.find("</figcaption>", p1)
                text = text[0: p1:] + text[p2 + len("</figcaption>")::]
                p1 = text.find("<figcaption>")
            pos_in_text = text.find(company)
            if pos_in_text == -1:
                continue
            else:
                links_for_analyze.add(link)
                bot.send_message(some_id, company + " was mentioned here\n" + url)

    # gathered all the links for analyse

    return bot.send_message(some_id, 'На сегодня всё!')


if __name__ == "__main__":
    finding_links_for_searching_names()
    schedule.every().day.at("18:14").do(finding_links_for_searching_names)
    Thread(target=schedule_checker).start()
