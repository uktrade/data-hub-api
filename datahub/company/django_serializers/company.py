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

    def handle_m2m_field(self, obj, field):
        """
        Custom handling of m2m fields. For most fields,
        return the default rendering from the super class.
        However:
        1. If the field name is 'future_interest_countries',
            instead call the get_active_future_export_countries method on the object,
            and return a list of ids of the countries thereby returned.
        """
        if field.name == 'future_interest_countries':
            self._current[field.name] = [
                self._value_from_field(value, value._meta.pk)
                for value in obj.get_active_future_export_countries()
            ]
        else:
            super().handle_m2m_field(obj, field)


def Deserializer(stream_or_string, **options):  # noqa: N802
    """
    TODO: Do we need this to work?
    """
    return JSONDeserializer(stream_or_string, **options)
