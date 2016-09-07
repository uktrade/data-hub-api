import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError

class Command(BaseCommand):

    help = 'Wait for db to be accessible'

    def handle(self, *args, **options):
        connected = False
        print("Waiting for db to start")
        while not connected:
            try:
                db_conn = connections['default']
                c = db_conn.cursor()
            except OperationalError as e:
                print(e)
                time.sleep(1)
                connected = False
            else:
                connected = True
        print("Db connection ready")
