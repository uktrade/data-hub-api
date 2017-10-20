import pytest

from datahub.company.models import Contact
from datahub.company.test.factories import ContactFactory
from ..models import Contact as ESContact

pytestmark = pytest.mark.django_db


def test_contact_dbmodel_to_dict(setup_es):
    """Tests conversion of db model to dict."""
    contact = ContactFactory()

    result = ESContact.dbmodel_to_dict(contact)

    keys = {'id', 'title', 'company', 'created_on',
            'modified_on', 'archived', 'archived_on',
            'archived_reason', 'archived_by', 'first_name',
            'last_name', 'job_title', 'adviser', 'primary',
            'telephone_countrycode', 'telephone_number',
            'email', 'address_same_as_company', 'address_1',
            'address_2', 'address_town', 'address_county',
            'address_country', 'address_postcode', 'telephone_alternative',
            'email_alternative', 'notes', 'contactable_by_dit',
            'contactable_by_dit_partners', 'contactable_by_email',
            'contactable_by_phone', 'company_sector', 'company_uk_region'}

    assert set(result.keys()) == keys


def test_contact_dbmodels_to_es_documents(setup_es):
    """Tests conversion of db models to Elasticsearch documents."""
    contacts = ContactFactory.create_batch(2)

    result = ESContact.dbmodels_to_es_documents(contacts)

    assert len(list(result)) == len(contacts)


def test_contact_dbmodels_to_es_documents_without_country(setup_es):
    """
    Tests conversion of db models to Elasticsearch documents when
    country is None.
    """
    # We want to bypass any validation
    contact = Contact(
        address_same_as_company=False,
        address_country=None
    )
    result = ESContact.es_document(contact)

    assert '_source' in result
