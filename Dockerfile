FROM python:3.12.8

# curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

EXPOSE 8000

RUN mkdir -p /app
WORKDIR /app

ADD requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

ADD . /app/

CMD ./start-dev.sh
