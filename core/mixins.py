"""General mixins."""

from core.utils import model_to_dictionary
from es.services import save_model
from korben.connector import Connector


class DeferredSaveModelMixin:
    """Handles add and update models."""

    def save(self, *args, **kwargs):
        """Save to Korben first, then alter the model instance with the data received back from Korben.

        Also (temporarily) write to ES."""
        self.clean()  # triggers custom validation
        update = True if self.id else False

        korben_connector = Connector(table_name=self._meta.db_table)
        korben_data = self._convert_model_to_korben_format()
        korben_response = korben_connector.post(data=korben_data, update=update)

        if korben_response:
            self._map_korben_response_to_model_instance()
            super().save(*args, **kwargs)

            # update ES
            save_model(self, update=update)

    def _map_korben_response_to_model_instance(self):
        """Override this method to control what needs to be converted back into the model."""
        raise NotImplementedError('This method must be implemented at the model class level.')

    def _convert_model_to_korben_format(self):
        """Override this method to have more granular control of what gets sent to Korben."""
        return model_to_dictionary(self, fk_ids=True)
