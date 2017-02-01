"""General mixins."""
from django.conf import settings
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from .utils import model_to_dictionary


class KorbenSaveModelMixin:
    """Handles custom validation and whether we save to Korben or not."""

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


class ArchivableViewSetMixin:
    """To be used with archivable models."""

    @detail_route(methods=['post'])
    def archive(self, request, pk):
        """Archive the object."""
        reason = request.data.get('reason', '')
        obj = self.get_object()
        obj.archive(user=request.user, reason=reason)
        serializer = self.read_serializer_class(obj)
        return Response(data=serializer.data)

    @detail_route(methods=['get'])
    def unarchive(self, request, pk):
        """Unarchive the object."""
        obj = self.get_object()
        obj.unarchive()
        serializer = self.read_serializer_class(obj)
        return Response(data=serializer.data)