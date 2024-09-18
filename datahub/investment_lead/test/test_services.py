import pytest

from django.db import IntegrityError

from datahub.company.models.company import Company
from datahub.company.test.factories import CompanyFactory
from datahub.company.models.contact import Contact
from datahub.company.test.factories import ContactFactory
from datahub.investment_lead.services import (
    add_new_company_from_eyb_lead,
    create_company_contact_for_eyb_lead,
    create_or_skip_eyb_lead_as_company_contact,
    email_matches_contact_on_eyb_lead_company,
    match_by_duns_number,
    process_eyb_lead,
)
from datahub.investment_lead.test.factories import EYBLeadFactory
from datahub.investment_lead.test.utils import (
    assert_eyb_lead_matches_company,
    assert_eyb_lead_matches_contact,
)


@pytest.mark.django_db
class TestEYBLeadServices:
    """Tests EYB Lead services"""

    def test_duns_number_matches_existing_company(self):
        company = CompanyFactory(duns_number='123456789')
        eyb_lead = EYBLeadFactory(duns_number='123456789')

        found, found_company = match_by_duns_number(eyb_lead.duns_number)

        assert found is True
        assert found_company.id == company.id

    def test_duns_number_does_not_match_company(self):
        CompanyFactory(duns_number='123456789')
        eyb_lead = EYBLeadFactory(duns_number='123456788')

        found, found_company = match_by_duns_number(eyb_lead.duns_number)

        assert found is False
        assert found_company is None

    def test_attach_existing_company_from_eyb_lead(self):
        company = CompanyFactory(duns_number='123456789')
        eyb_lead = EYBLeadFactory(duns_number='123456789')

        result = process_eyb_lead(eyb_lead)

        assert eyb_lead.company is not None
        assert eyb_lead.company == company
        assert company == result

    def test_add_new_company_from_eyb_lead(self):
        eyb_lead = EYBLeadFactory(duns_number=None)

        company = process_eyb_lead(eyb_lead)

        company = Company.objects.get(pk=company.pk)
        assert_eyb_lead_matches_company(company, eyb_lead)

        assert eyb_lead.company == company

    def test_add_new_company_without_company_name_fails(self):
        eyb_lead = EYBLeadFactory(duns_number=None)
        eyb_lead.company_name = None

        with pytest.raises(IntegrityError):
            add_new_company_from_eyb_lead(eyb_lead)

    def test_add_new_company_without_address_country_none_fails(self):
        eyb_lead = EYBLeadFactory(duns_number=None)
        eyb_lead.address_county = None

        with pytest.raises(IntegrityError):
            add_new_company_from_eyb_lead(eyb_lead)

    def test_existing_company_match_contact_on_email_address(self):
        """
        Match email address for contact associated with EYB Lead company
        """
        contact = ContactFactory()
        eyb_lead_matching = EYBLeadFactory(
            company=contact.company,
            email=contact.email,
            full_name=contact.name,
        )
        eyb_lead_matching.save()
        contact.save()

        result = email_matches_contact_on_eyb_lead_company(eyb_lead_matching)

        assert result

    def test_fail_match_on_partial_email(self):
        """
        Do not match an email address that is a subset of email address
        where other parameters match.
        """
        contact = ContactFactory()
        eyb_lead_not_matching = EYBLeadFactory(
            company=contact.company,
            email=f"notmatch.{contact.email}",
            full_name=contact.name,
        )
        eyb_lead_not_matching.save()
        contact.save()

        result = email_matches_contact_on_eyb_lead_company(eyb_lead_not_matching)

        assert not result

    def test_fail_match_for_different_company(self):
        """
        Do not match contact with a matching email address belonging to a different company
        """
        contact = ContactFactory()
        eyb_lead_not_matching = EYBLeadFactory(
            email=contact.email,
            full_name=contact.name,
        )
        eyb_lead_not_matching.save()
        contact.save()

        result = email_matches_contact_on_eyb_lead_company(eyb_lead_not_matching)

        assert not result

    def test_create_contact_on_company(self):
        eyb_lead = EYBLeadFactory()
        contact = create_company_contact_for_eyb_lead(eyb_lead)

        contact = Contact.objects.get(pk=contact.pk)

        assert contact.company == eyb_lead.company
        assert_eyb_lead_matches_contact(contact, eyb_lead)

    def test_eyb_lead_has_no_company_set(self):
        eyb_lead = EYBLeadFactory()
        eyb_lead.company = None

        with pytest.raises(AttributeError):
            create_or_skip_eyb_lead_as_company_contact(eyb_lead)
