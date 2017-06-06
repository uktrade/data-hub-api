from unittest import mock

import pytest

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.search import models

pytestmark = pytest.mark.django_db


def test_id_name_dict():
    """Tests _id_name_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.name = 'test'

    res = models._id_name_dict(obj)

    assert res == {
        'id': str(obj.id),
        'name': obj.name,
    }


def test_id_type_dict():
    """Tests _id_type_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.type = 'test'

    res = models._id_type_dict(obj)

    assert res == {
        'id': str(obj.id),
        'type': obj.type,
    }


def test_contact_dict():
    """Tests contact_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.first_name = 'First'
    obj.last_name = 'Last'

    res = models._contact_dict(obj)

    assert res == {
        'id': str(obj.id),
        'first_name': obj.first_name,
        'last_name': obj.last_name,
    }


def test_company_dict():
    """Tests company_dict."""
    obj = mock.Mock()
    obj.id = 123
    obj.company_number = '01234567'

    res = models._company_dict(obj)

    assert res == {
        'id': str(obj.id),
        'company_number': obj.company_number,
    }


def test_company_dbmodel_to_dict():
    """Tests conversion of db model to dict."""
    company = CompanyFactory()

    result = models.Company.dbmodel_to_dict(company)

    keys = {'business_type', 'registered_address_country',
            'sector', 'trading_address_country', 'uk_region',
            'contacts', 'id', 'uk_based', 'export_to_countries',
            'future_interest_countries', 'created_on',
            'modified_on', 'archived', 'archived_on',
            'archived_reason', 'archived_by', 'name',
            'registered_address_1', 'registered_address_2',
            'registered_address_3', 'registered_address_4',
            'registered_address_town', 'registered_address_county',
            'registered_address_postcode', 'company_number', 'alias',
            'employee_range', 'turnover_range', 'account_manager',
            'lead', 'description', 'website', 'trading_address_1',
            'trading_address_2', 'trading_address_3',
            'trading_address_4', 'trading_address_town',
            'trading_address_county', 'trading_address_postcode',
            'headquarter_type', 'classification', 'parent',
            'one_list_account_owner', 'level'}

    assert set(result.keys()) == keys


def test_company_dbmodels_to_es_documents():
    """Tests conversion of db models to Elasticsearch documents."""
    companies = (CompanyFactory(), CompanyFactory(),)

    result = models.Company.dbmodels_to_es_documents(companies)

    assert len(list(result)) == len(companies)


def test_contact_dbmodel_to_dict():
    """Tests conversion of db model to dict."""
    contact = ContactFactory()

    result = models.Contact.dbmodel_to_dict(contact)

    keys = {'id', 'title', 'company', 'created_on',
            'modified_on', 'archived', 'archived_on',
            'archived_reason', 'archived_by', 'first_name',
            'last_name', 'job_title', 'adviser', 'primary',
            'telephone_countrycode', 'telephone_number',
            'email', 'address_same_as_company', 'address_1',
            'address_2', 'address_3', 'address_4',
            'address_town', 'address_county', 'address_country',
            'address_postcode', 'telephone_alternative',
            'email_alternative', 'notes', 'contactable_by_dit',
            'contactable_by_dit_partners', 'contactable_by_email',
            'contactable_by_phone'}

    assert set(result.keys()) == keys


def test_contact_dbmodels_to_es_documents():
    """Tests conversion of db models to Elasticsearch documents."""
    contacts = (ContactFactory(), ContactFactory(),)

    result = models.Contact.dbmodels_to_es_documents(contacts)

    assert len(list(result)) == len(contacts)
