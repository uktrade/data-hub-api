import logging

import reversion
from django.db.models import Q
from rest_framework import serializers

from datahub.ingest.boto3 import S3ObjectProcessor
from datahub.ingest.tasks import (
    BaseObjectIdentificationTask,
    BaseObjectIngestionTask,
)
from datahub.investment_lead.models import EYBLead

logger = logging.getLogger(__name__)


class BaseEYBIdentificationTask(BaseObjectIdentificationTask):
    """Base class to identify new EYB objects in S3 and determine if they should be ingested."""


class BaseEYBIngestionTask(BaseObjectIngestionTask):
    """Class to ingest a specific EYB object from S3."""

    def __init__(
        self,
        object_key: str,
        s3_processor: S3ObjectProcessor,
        serializer_class: serializers.Serializer,
    ) -> None:
        self.serializer_class = serializer_class
        super().__init__(object_key, s3_processor)

    def _get_hashed_uuid(self, record: dict) -> str:
        """Gets the hashed uuid from the incoming record."""
        return record['hashedUuid']

    def _get_record_from_line(self, deserialized_line: dict) -> dict:
        """Extracts the record from the deserialized line."""
        return deserialized_line['object']

    def _process_record(self, record: dict) -> None:
        """Processes a single record.

        This method should take a single record, update an existing instance,
        or create a new one, and return None.
        """
        serializer = self.serializer_class(data=record)
        if serializer.is_valid():
            hashed_uuid = self._get_hashed_uuid(record)
            with reversion.create_revision():
                queryset = EYBLead.objects.filter(
                    Q(user_hashed_uuid=hashed_uuid)
                    | Q(triage_hashed_uuid=hashed_uuid)
                    | Q(marketing_hashed_uuid=hashed_uuid),
                )
                instance, created = queryset.update_or_create(defaults=serializer.validated_data)
            if created:
                self.created_ids.append(str(instance.id))
            else:
                self.updated_ids.append(str(instance.id))
        else:
            self.errors.append(
                {
                    'record': record,
                    'errors': serializer.errors,
                },
            )
