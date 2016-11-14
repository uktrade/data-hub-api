FROM python:3.5

RUN git clone https://github.com/uktrade/data-hub-dummy-korben.git
WORKDIR data-hub-dummy-korben
RUN pip install -r requirements.txt
CMD python app.py

EXPOSE 8080
