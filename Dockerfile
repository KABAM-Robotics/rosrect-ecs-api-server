FROM python:3.6.10

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

ADD ecs_api_server /ecs_api_server

ENTRYPOINT [ "python3" ]