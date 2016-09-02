from rest_framework import serializers
from api.models.company import Company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = (
            'id',
            'company_number',
            'uk_based',
            'business_type',
            'registered_name',
            'trading_name',
            'sectors',
            'website',
            'number_of_employees',
            'annual_turnover',
            'trading_address_1',
            'trading_address_2',
            'trading_address_town',
            'trading_address_county',
            'trading_address_country',
            'trading_address_postcode',
            'region',
            'account_manager',
            'countries_of_interest',
            'currently_exporting_to',
            'connections'
        )
