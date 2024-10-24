import pytest

from django.db import IntegrityError

from datahub.company.models.company import Company
from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.investment_lead import services
from datahub.investment_lead.services import (
    add_new_company_from_eyb_lead,
    create_or_skip_eyb_lead_as_company_contact,
    email_matches_contact_on_eyb_lead_company,
    find_match_by_duns_number,
    get_leads_to_process,
    link_leads_to_companies,
    match_or_create_company_for_eyb_lead,
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

        found_company = find_match_by_duns_number(eyb_lead.duns_number)

        assert found_company.id == company.id

    def test_duns_number_does_not_match_company(self):
        CompanyFactory(duns_number='123456789')
        eyb_lead = EYBLeadFactory(duns_number='123456788')

        found_company = find_match_by_duns_number(eyb_lead.duns_number)

        assert found_company is None

    def test_attach_existing_company_from_eyb_lead(self):
        company = CompanyFactory(duns_number='123456789')
        eyb_lead = EYBLeadFactory(duns_number='123456789')

        result = match_or_create_company_for_eyb_lead(eyb_lead)

        assert eyb_lead.company is not None
        assert eyb_lead.company == company
        assert company == result

    def test_add_new_company_from_eyb_lead(self):
        eyb_lead = EYBLeadFactory(duns_number=None)

        company = match_or_create_company_for_eyb_lead(eyb_lead)

        company = Company.objects.get(pk=company.pk)
        assert_eyb_lead_matches_company(company, eyb_lead)

        assert eyb_lead.company == company

    @pytest.mark.parametrize(
        'function_to_test',
        [
            'raise_exception_for_eyb_lead_without_company',
            'email_matches_contact_on_eyb_lead_company',
            'create_or_skip_eyb_lead_as_company_contact',
            'create_company_contact_for_eyb_lead',
        ],
    )
    def test_exception_raised_when_company_is_none(self, function_to_test):
        eyb_lead = EYBLeadFactory()
        eyb_lead.company = None

        with pytest.raises(AttributeError):
            getattr(services, function_to_test)(eyb_lead)

    def test_add_new_company_without_company_name_fails(self):
        eyb_lead = EYBLeadFactory(duns_number=None)
        eyb_lead.company_name = None

        with pytest.raises(IntegrityError):
            add_new_company_from_eyb_lead(eyb_lead)

    def test_add_new_company_without_address_country_fails(self):
        eyb_lead = EYBLeadFactory(duns_number=None)
        eyb_lead.address_country = None

        with pytest.raises(ValueError):
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
            email=f'notmatch.{contact.email}',
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

    def test_skip_creation_when_contact_exists(self):
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
        count = eyb_lead_matching.company.contacts.count()

        create_or_skip_eyb_lead_as_company_contact(eyb_lead_matching)

        assert eyb_lead_matching.company.contacts.count() == count
        assert eyb_lead_matching.company.contacts.first() == contact

    def test_create_contact_on_company(self):
        eyb_lead = EYBLeadFactory()
        count = eyb_lead.company.contacts.count()

        create_or_skip_eyb_lead_as_company_contact(eyb_lead)

        assert eyb_lead.company.contacts.count() == count + 1
        contact = eyb_lead.company.contacts.first()
        assert_eyb_lead_matches_contact(contact, eyb_lead)

    def test_get_leads_to_process(self):
        # Not returned in the results
        company = CompanyFactory()
        EYBLeadFactory(company=company)

        # Returned in the results
        expected_eyb_lead = EYBLeadFactory(
            company=None,
            triage_hashed_uuid='123123123',
            user_hashed_uuid='123123123',
        )

        # only one result is expected
        result = get_leads_to_process()

        assert result.count() == 1
        tester = result[0]
        assert tester == expected_eyb_lead
        assert tester.company is None

    def test_link_leads_to_companies(self):
        eyb_lead = EYBLeadFactory(
            duns_number='123',
            company=None,
            triage_hashed_uuid='123123123',
            user_hashed_uuid='123123123',
        )
        company = CompanyFactory(duns_number='123')

        assert eyb_lead.company is None

        # link company and create contact
        link_leads_to_companies()

        # company linked assertions
        assert eyb_lead.company is not None
        assert eyb_lead.company == company

        # contact linked assertions
        assert eyb_lead.company.contacts.count() == 1
        contact = eyb_lead.company.contacts.first()
        assert_eyb_lead_matches_contact(contact, eyb_lead)
