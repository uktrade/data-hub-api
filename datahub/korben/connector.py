"""Talk to Korben API for saving."""

import requests
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from raven.contrib.django.raven_compat.models import client

from datahub.korben.exceptions import KorbenException
from .utils import generate_signature


class KorbenConnector:
    """Korben connector."""

    default_headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json',
    }

    def __init__(self):
        """Initalise the connector."""
        self._json_encoder = DjangoJSONEncoder()
        self.base_url = '{host}:{port}'.format(
            host=self.handle_host(settings.KORBEN_HOST),
            port=settings.KORBEN_PORT)

    @staticmethod
    def handle_host(host):
        """Add the protocol if not specified."""
        if 'http://' in host or 'https://' in host:
            return host
        else:
            return 'http://{host}'.format(host=host)

    def encode_json_bytes(self, model_dict):
        """Encode json into byte."""
        json_str = self._json_encoder.encode(model_dict)
        return bytes(json_str, 'utf-8')

    def inject_auth_header(self, url, body):
        """Add the signature into the header."""
        self.default_headers['X-Signature'] = generate_signature(
            url, body, settings.DATAHUB_SECRET)

    def post(self, data, table_name, update=False):
        """Perform POST operations: create and update.

        :param data: dict object containing the data to be passed to Korben
        :param update: whether the POST request has to be treated as an UPDATE
        :return: requests Response object
        """
        if update:
            url = '{base_url}/update/{table_name}/'.format(
                base_url=self.base_url, table_name=table_name)
        else:
            url = '{base_url}/create/{table_name}/'.format(
                base_url=self.base_url, table_name=table_name)

        data = self.encode_json_bytes(data)
        self.inject_auth_header(url, data)
        response = requests.post(
            url=url, data=data, headers=self.default_headers)
        if response.ok:
            return response
        else:
            raise KorbenException(message=response.content)

    def get(self, data, table_name):
        """Get single object from Korben.

        :param object_id: object id
        :return: requests Response object
        """
        url = '{base_url}/get/{table_name}/{id}/'.format(
            base_url=self.base_url, table_name=table_name, id=data['id'])
        data = self.encode_json_bytes(data)
        self.inject_auth_header(url, data)
        response = requests.post(
            url=url, data=data, headers=self.default_headers)
        return response

    def validate_credentials(self, username, password):
        """Validate CDMS User credentials.

        :param username: str
        :param password: str
        :return: boolean success or fail, None if CDMS/Korben communication fails
        """
        url = '{base_url}/auth/validate-credentials/'.format(
            base_url=self.base_url,)
        data = self.encode_json_bytes(
            dict(username=username, password=password))
        self.inject_auth_header(url, data)
        try:
            response = requests.post(
                url=url, data=data, headers=self.default_headers)
            if response.ok:
                return response.json()  # Returns JSON encoded boolean
            else:
                return None
        except (requests.RequestException, ValueError):
            client.captureException()
            return None

    def ping(self):
        """Perform the Korben ping."""
        url = '{base_url}/ping.xml'.format(base_url=self.base_url,)
        try:
            response = requests.get(url=url)
            return response
        except requests.RequestException:  # Exception handling the request
            client.captureException()
            return False
