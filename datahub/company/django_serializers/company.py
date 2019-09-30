from django.core.serializers.json import (
    Serializer as JSONSerializer,
    Deserializer as JSONDeserializer,
)


class Serializer(JSONSerializer):
    def handle_m2m_field(self, obj, field):
        if field.name == 'future_interest_countries':
            self._current[field.name] = [
                self._value_from_field(value, value._meta.pk)
                for value in obj.get_active_future_export_countries()
            ]
        else:
            super().handle_m2m_field(obj, field)


class Deserializer(JSONSerializer):
    pass
