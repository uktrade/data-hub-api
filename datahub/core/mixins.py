"""General mixins."""

import reversion
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
        super(DeferredSaveModelMixin, self).__init__(*args, **kwargs)

    def save(self, as_korben=False, *args, **kwargs):
        """Save to Korben first, then alter the model instance with the data received back from Korben.

        We force feed an ID to Django, so we cannot differentiate between update or create without querying the db
        https://docs.djangoproject.com/en/1.10/ref/models/instances/#how-django-knows-to-update-vs-insert

        :param as_korben: bool - Whether or not the data comes from Korben, in that case don't trigger validation
        """

        if not as_korben:
            self.clean()  # triggers custom validation
            # objects is not accessible via instances
            update = type(self).objects.filter(id=self.id).exists()
            korben_data = self._convert_model_to_korben_format()
            korben_response = self.korben_connector.post(data=korben_data, update=update)
            self._map_korben_response_to_model_instance(korben_response)

        super().save(*args, **kwargs)

    def _map_korben_response_to_model_instance(self, korben_response):
        """Override this method to control what needs to be converted back into the model."""

        if korben_response.status_code == status.HTTP_200_OK:
            for key, value in korben_response.json().items():
                setattr(self, key, value)
        elif korben_response.status_code == status.HTTP_404_NOT_FOUND:
            return
        else:
            raise KorbenException(korben_response.json())

    def get_excluded_fields(self):
        """Override this method to define which fields should not be send to Korben."""
        return []

    def _convert_model_to_korben_format(self):
        """Override this method to have more granular control of what gets sent to Korben."""

        return model_to_dictionary(self, excluded_fields=self.get_excluded_fields(), fk_ids=True)

    def update_from_korben(self):
        """Update the model fields from Korben.

        :return the new instance
        """
        with reversion.create_revision():
            korben_data = self._convert_model_to_korben_format()
            korben_response = self.korben_connector.get(data=korben_data)
            self._map_korben_response_to_model_instance(korben_response)
            self.save(as_korben=True)

            reversion.set_user(get_korben_user())
            reversion.set_comment('Updated by Korben')
        return self
