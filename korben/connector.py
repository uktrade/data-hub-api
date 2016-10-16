"""Talk to Korben API for saving."""

import json
import uuid

from django.conf import settings

import requests

class KorbenJSONEncoder(json.JSONEncoder):

    handlers = {
        uuid.UUID: str
    }

    def default(self, obj):
        handler = self.handlers.get(type(obj))
        if handler: return handler(obj)
        return super().default(obj)


class Connector:

    default_headers = {
        'Content-type': 'application/json',
    }

    def __init__(self, table_name):
        self.encode_json = KorbenJSONEncoder().encode
        self.table_name = table_name
        self.base_url = 'http://{host}:{port}'.format(host=settings.KORBEN_HOST, port=settings.KORBEN_PORT)

    def post(self, data, update=False):
        """Perform POST operations: create and update.

        :param data: dict object containing the data to be passed to Korben
        :param update: whether the POST request has to be treated as an UPDATE
        :return: requests Response object
        """
        if update:
            url = '{base_url}/update/{table_name}/{id}'.format(
                base_url=self.base_url,
                table_name=self.table_name,
                id=data['id']
            )
        else:
            url = '{base_url}/create/{table_name}'.format(
                base_url=self.base_url,
                table_name=self.table_name
            )

        response = requests.post(
            url=url, data=self.encode_json(data), headers=self.default_headers
        )
        return response

    def get(self, data):
        """Get single object from Korben.

        :param data: dict object containing the data to be passed to Korben
        :return: requests Response object
        """
        url = '{base_url}/get/{table_name}/{id}'.format(
            base_url=self.base_url,
            table_name=self.table_name,
            id=data['id']
        )
        response = requests.get(url)
        return response
