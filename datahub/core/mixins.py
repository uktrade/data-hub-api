"""General mixins."""

import reversion
from dateutil import parser
from raven.contrib.django.raven_compat.models import client
from rest_framework import status

from datahub.korben.connector import KorbenConnector
from datahub.korben.exceptions import KorbenException
from datahub.korben.utils import get_korben_user

from .utils import model_to_dictionary


class DeferredSaveModelMixin:
    """Handles add and update models."""

    def __init__(self, *args, **kwargs):
        """Add third part services connectors to the instance."""
        self.korben_connector = KorbenConnector(table_name=self._meta.db_table)
        self.model = type(self)  # get the class from the instance
        super(DeferredSaveModelMixin, self).__init__(*args, **kwargs)

    def save(self, as_korben=False, **kwargs):
        """
        Override the Django save implementation to save to Korben.

        :param as_korben: bool - Whether or not the data comes from Korben, in that case don't trigger validation
        """
        if not as_korben:
            self._save_to_korben()
        super().save(**kwargs)

    def _save_to_korben(self):
        """
        Save to Korben first, then alter the model instance with the data received back from Korben.

        We force feed an ID to Django, so we cannot differentiate between update or create without querying the db
        https://docs.djangoproject.com/en/1.10/ref/models/instances/#how-django-knows-to-update-vs-insert
        """
        self.clean()  # triggers custom validation
        update = self.model.objects.filter(id=self.id).exists()
        korben_data = self._convert_model_to_korben_format()
        korben_response = self.korben_connector.post(data=korben_data, update=update)
        self._map_korben_response_to_model_instance(korben_response)

    def _map_korben_response_to_model_instance(self, korben_response):
        """Override this method to control what needs to be converted back into the model."""
        if korben_response.status_code == status.HTTP_200_OK:
            json_data = korben_response.json()

            for key, value in json_data.items():
                setattr(self, key, value)

            for name in filter(lambda v: v in json_data, self.get_datetime_fields()):
                value = json_data[name]
                setattr(self, name, parser.parse(value) if value else value)

    def get_excluded_fields(self):
        """Override this method to define which fields should not be send to Korben."""
        return []

    def get_datetime_fields(self):
        """Return list of fields that should be mapped as datetime."""
        return []

    def _convert_model_to_korben_format(self):
        """Override this method to have more granular control of what gets sent to Korben."""
        return model_to_dictionary(self, excluded_fields=self.get_excluded_fields(), fk_ids=True)

    def _korben_response_same_as_model(self, korben_response):
        """Check whether the korben response and the model have the same values.

        :return True if the model and the korben response are the same, otherwise False
        """
        for key, value in korben_response.json().items():
            if str(getattr(self, key)) != value:
                return False
        return True

    def update_from_korben(self):
        """Update the model fields from Korben.

        :return the model instance
        """
        korben_data = self._convert_model_to_korben_format()
        korben_response = self.korben_connector.get(data=korben_data)

        if korben_response.status_code == status.HTTP_200_OK:
            if not self._korben_response_same_as_model(korben_response):
                with reversion.create_revision():
                    self._map_korben_response_to_model_instance(korben_response)
                    self.save(as_korben=True)
                    reversion.set_user(get_korben_user())
                    reversion.set_comment('Updated by Korben')
        elif korben_response.status_code == status.HTTP_404_NOT_FOUND:
            pass
        else:
            client.captureException(korben_response.json())
            raise KorbenException(korben_response.json())
        return self
