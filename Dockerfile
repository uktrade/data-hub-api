FROM python:3.5

RUN mkdir -p /shared
RUN mkdir -p /app
WORKDIR /app

ADD requirements.txt .
RUN pip install -r requirements.txt

# Install dockerize https://github.com/jwilder/dockerize
RUN apt-get update && apt-get install -y wget

ENV DOCKERIZE_VERSION v0.2.0
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

ADD . /app/

RUN chmod a+x start.sh

ENV ES_PORT 9200
ENV ES_HOST es
ENV KORBEN_HOST korben
ENV KORBEN_PORT 8080
ENV DEBUG False
ENV ES_ACCESS True
ENV COVERAGE_FILE '/shared/.coverage'


EXPOSE 8000
CMD ./start.sh
