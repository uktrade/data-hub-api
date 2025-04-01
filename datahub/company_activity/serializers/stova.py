from rest_framework import serializers

from datahub.company_activity.models.stova_event import StovaEvent


class StovaEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = StovaEvent
        fields = [
            # Reverse FK to data hub `Event`
            'datahub_event',
            'id',
            'stova_event_id',
            'name',
            'description',
            'code',
            'created_by',
            'modified_by',
            'client_contact',
            'contact_info',
            'country',
            'city',
            'state',
            'timezone',
            'url',
            'max_reg',
            'created_date',
            'modified_date',
            'start_date',
            'live_date',
            'close_date',
            'end_date',
            'location_state',
            'location_country',
            'location_address1',
            'location_address2',
            'location_address3',
            'location_city',
            'location_name',
            'location_postcode',
            'approval_required',
            'price_type',
            'folder_id',
            'default_language',
            'standard_currency',
        ]
