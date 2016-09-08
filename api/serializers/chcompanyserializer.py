from rest_framework import serializers
from api.models.chcompany import CHCompany


class CHCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = CHCompany
        fields = (
            'company_number',
            'company_name',
            'registered_address_care_of',
            'registered_address_po_box',
            'registered_address_address_1',
            'registered_address_address_2',
            'registered_address_town',
            'registered_address_county',
            'registered_address_country',
            'registered_address_postcode',
            'company_category',
            'company_status',
            'sic_code_1',
            'sic_code_2',
            'sic_code_3',
            'sic_code_4',
            'uri',
        )
