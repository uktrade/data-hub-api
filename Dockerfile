FROM python:3.5

RUN mkdir -p /app/leeloo
WORKDIR /app/leeloo

ADD requirements.txt .
RUN pip install -r requirements.txt

RUN git clone https://github.com/uktrade/data-hub-backend.git
RUN pip install -e data-hub-backend/korben

ADD . /app/leeloo/

RUN chmod a+x start.sh

ENV ES_PORT 9200
ENV ES_HOST es
ENV DEBUG True
ENV ES_ACCESS True

EXPOSE 8000
CMD ./start.sh
