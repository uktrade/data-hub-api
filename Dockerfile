FROM python:3.5

RUN mkdir -p /app/leeloo
WORKDIR /app/leeloo

ADD requirements.txt .
RUN pip install -r requirements.txt

ADD . /app/leeloo

RUN chmod a+x docker-entrypoint.sh
ENTRYPOINT ["./docker-entrypoint.sh"]

ENV ES_PORT 9200
ENV ES_HOST es

EXPOSE 8000
