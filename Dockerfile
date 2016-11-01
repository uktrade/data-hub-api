FROM python:3.5

RUN mkdir -p /app/leeloo
WORKDIR /app/leeloo

ADD requirements.txt .
RUN pip install -r requirements.txt

RUN git clone https://github.com/uktrade/data-hub-backend.git
RUN pip install -e data-hub-backend/korben

# Install dockerize https://github.com/jwilder/dockerize
RUN apt-get update && apt-get install -y wget

ENV DOCKERIZE_VERSION v0.2.0
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

ADD . /app/leeloo/

RUN chmod a+x start.sh

ENV ES_PORT 9200
ENV ES_HOST es
ENV KORBEN_HOST korben
ENV KORBEN_PORT 8080
ENV DEBUG False
ENV ES_ACCESS True



EXPOSE 8000
CMD ./start.sh
