"""General mixins."""

from datahub.korben.connector import KorbenConnector

from .utils import model_to_dictionary


class DeferredSaveModelMixin:
    """Handles add and update models."""

    def __init__(self, *args, **kwargs):
        """Add third part services connectors to the instance."""
        self.korben_connector = KorbenConnector()
        self.model = type(self)  # get the class from the instance
        super().__init__(*args, **kwargs)

    def _get_table_name_from_model(self):
        """Get table name from model."""
        return self._meta.db_table

    def save(self, skip_custom_validation=False, **kwargs):
        """Override the Django save implementation to save to Korben."""
        if not skip_custom_validation:
            self.clean()
        super().save(**kwargs)

    def get_excluded_fields(self):
        """Override this method to define which fields should not be send to Korben."""
        return []

    def get_datetime_fields(self):
        """Return list of fields that should be mapped as datetime."""
        return []

    def convert_model_to_korben_format(self):
        """Override this method to have more granular control of what gets sent to Korben."""
        return model_to_dictionary(self, excluded_fields=self.get_excluded_fields(), expand_foreign_keys=False)

    def _korben_response_same_as_model(self, korben_response):
        """Check whether the korben response and the model have the same values.

        :return True if the model and the korben response are the same, otherwise False
        """
        for key, value in korben_response.json().items():
            if str(getattr(self, key)) != value:
                return False
        return True
