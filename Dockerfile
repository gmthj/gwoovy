FROM python:3.10
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
# FROM ubuntu:20.04 AS runner-image
RUN apt-get -y update && apt-get -y upgrade && apt-get install -y ffmpeg && apt-get install -y libopus0
COPY . /bot
CMD python bot3-music.py