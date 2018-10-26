from rest_framework import serializers

from datahub.core.serializers import RelaxedDateTimeField


class TimelineEventSerializer(serializers.Serializer):
    """Company timeline event serialiser."""

    data_source = serializers.CharField()
    data_source_label = serializers.CharField()
    datetime = RelaxedDateTimeField()
    description = serializers.CharField()
