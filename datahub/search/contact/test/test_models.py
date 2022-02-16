import pytest

from datahub.company.models import Contact
from datahub.company.test.factories import ContactFactory
from datahub.search.contact.models import Contact as SearchContact

pytestmark = pytest.mark.django_db


def test_contact_dbmodel_to_dict(opensearch):
    """Tests conversion of db model to dict."""
    contact = ContactFactory()

    result = SearchContact.db_object_to_dict(contact)

    keys = {
        '_document_type',
        'id',
        'title',
        'company',
        'created_on',
        'created_by',
        'modified_on',
        'archived',
        'archived_on',
        'archived_reason',
        'archived_by',
        'first_name',
        'last_name',
        'name',
        'name_with_title',
        'job_title',
        'adviser',
        'primary',
        'telephone_countrycode',
        'full_telephone_number',
        'telephone_number',
        'email',
        'address_same_as_company',
        'address_1',
        'address_2',
        'address_area',
        'address_town',
        'address_county',
        'address_country',
        'address_postcode',
        'telephone_alternative',
        'email_alternative',
        'notes',
        'company_sector',
        'company_uk_region',
    }

    assert set(result.keys()) == keys


def test_contact_dbmodels_to_documents(opensearch):
    """Tests conversion of db models to OpenSearch documents."""
    contacts = ContactFactory.create_batch(2)

    result = SearchContact.db_objects_to_documents(contacts)

    assert len(list(result)) == len(contacts)


def test_contact_dbmodels_to_document_without_country(opensearch):
    """
    Tests conversion of db models to OpenSearch documents when
    country is None.
    """
    # We want to bypass any validation
    contact = Contact(
        address_same_as_company=False,
        address_country=None,
    )
    result = SearchContact.to_document(contact)

    assert '_source' in result
