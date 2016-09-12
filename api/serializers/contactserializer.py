from rest_framework import serializers
from api.models.contact import Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = (
            'id',
            'title',
            'first_name',
            'last_name',
            'role',
            'phone',
            'email',
            'address_1',
            'address_2',
            'address_town',
            'address_county',
            'address_postcode',
            'address_country',
            'alt_phone',
            'alt_email',
            'notes',
            'company',
            'primary_contact_team',
            'interactions',
            'created_date',
            'modified_date',
        )
        depth = 1


class ContactSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = (
            'id',
            'title',
            'first_name',
            'last_name',
            'role',
            'phone',
            'email',
            'address_1',
            'address_2',
            'address_town',
            'address_county',
            'address_postcode',
            'address_country',
            'alt_phone',
            'alt_email',
            'notes',
            'company',
            'primary_contact_team'
        )
