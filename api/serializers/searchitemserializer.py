from rest_framework import serializers


class SearchItemSerializer(serializers.Serializer):
    source_id = serializers.CharField(max_length=20)
    result_source = serializers.CharField(max_length=20)
    result_type = serializers.CharField(max_length=20)
    title = serializers.CharField(max_length=160)
    address_1 = serializers.CharField(max_length=160)
    address_2 = serializers.CharField(max_length=160)
    address_town = serializers.CharField(max_length=160)
    address_county = serializers.CharField(max_length=160)
    address_country = serializers.CharField(max_length=160)
    address_postcode = serializers.CharField(max_length=20)
    alt_title = serializers.CharField(max_length=160)
    alt_address_1 = serializers.CharField(max_length=160)
    alt_address_2 = serializers.CharField(max_length=160)
    alt_address_town = serializers.CharField(max_length=160)
    alt_address_county = serializers.CharField(max_length=160)
    alt_address_country = serializers.CharField(max_length=160)
    alt_address_postcode = serializers.CharField(max_length=20)
    company_number = serializers.CharField(max_length=20)
    incorporation_date = serializers.DateField()
