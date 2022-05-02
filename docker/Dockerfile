FROM python:latest
ARG TELEGRAM_BOT_TOKEN
ENV TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
ARG YANDEX_TOKEN
ENV YANDEX_TOKEN=$YANDEX_TOKEN
RUN mkdir -p /app
WORKDIR /app
COPY ./docker/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD [ "python", "src/main.py" ]