FROM python:latest
RUN mkdir -p /app
WORKDIR /app
COPY ./docker/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD [ "python", "src/main.py" ]