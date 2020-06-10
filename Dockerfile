FROM python:3.8

# libyaml-dev is required for watchdog (celery auto-reloader)
RUN apt-get update && apt-get install -y wget libyaml-dev

# Install dockerize https://github.com/jwilder/dockerize
ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

EXPOSE 8000

RUN mkdir -p /app
WORKDIR /app

ADD requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ADD . /app/

CMD ./start.sh
