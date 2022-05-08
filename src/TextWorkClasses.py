import re
import pickle
from threading import Lock
from YandexDiskWorkClass import YandexDiskWork

mutex = Lock()


class TextAnalyzing:

    def __init__(self):
        YandexDiskWork().download_file("https://disk.yandex.ru/d/UtfYbeYZ7FORQQ", "NLP.pkl")
        with open('./src/NLP.pkl', 'rb') as f:
            self.tfidf_transformer, self.clf = pickle.load(f)
        f.close()

    def nlp_analyze(self, text):
        """rating the text"""
        x_test_tfidf = self.tfidf_transformer.transform([text.lower()])
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
