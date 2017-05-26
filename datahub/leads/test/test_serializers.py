"""Tests for business lead serialisers."""

import pytest

from datahub.leads.serializers import BusinessLeadSerializer
from datahub.leads.test.factories import BusinessLeadFactory

pytestmark = pytest.mark.django_db


def test_no_contact_details_update():
    lead = BusinessLeadFactory()
    data = {
        'email': None,
        'telephone_number': None
    }
    serializer = BusinessLeadSerializer(lead, data)

    assert not serializer.is_valid()
    assert serializer.errors == {
        'email': ['Email address or phone number required'],
        'telephone_number': ['Email address or phone number required']
    }


def test_no_name_update():
    lead = BusinessLeadFactory()
    data = {
        'first_name': None,
        'last_name': None,
        'company_name': None,
        'company': None,
    }
    serializer = BusinessLeadSerializer(lead, data)

    assert not serializer.is_valid()
    assert serializer.errors == {
        'first_name': ['Company name or first name and last name required'],
        'last_name': ['Company name or first name and last name required'],
        'company_name': ['Company name or first name and last name required']
    }


def test_no_name_contact_create():
    data = {}
    serializer = BusinessLeadSerializer(data=data)

    assert not serializer.is_valid()
    assert serializer.errors == {
        'email': ['Email address or phone number required'],
        'telephone_number': ['Email address or phone number required'],
        'first_name': ['Company name or first name and last name required'],
        'last_name': ['Company name or first name and last name required'],
        'company_name': ['Company name or first name and last name required']
    }
