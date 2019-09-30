from django.core.serializers.json import (
    Deserializer as JSONDeserializer,
    Serializer as JSONSerializer,
)


class Serializer(JSONSerializer):
    """
    Serializer to customise the way we store companies in reversion Versions.
    1. Change future_interest_countries field in the serialised format to a list
        of IDs of countries returned by the get_active_future_export_countries method on the
        company.
    """

    def end_object(self, obj):
        """
        Change the serialized data for the future_interest_countries field,
        and then call end_object on the super class.
        """
        self._current['future_interest_countries'] = [
            self._value_from_field(value, value._meta.pk)
            for value in obj.get_active_future_export_countries()
        ]
        return super().end_object(obj)


def Deserializer(stream_or_string, **options):  # noqa: N802
    """
    TODO: Do we need this to work?
    """
    return JSONDeserializer(stream_or_string, **options)
