FROM python:3.6

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
RUN chmod a+x tests.sh

EXPOSE 8000
CMD ./start.sh
