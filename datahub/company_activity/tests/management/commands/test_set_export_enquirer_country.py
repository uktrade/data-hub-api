import logging
from unittest.mock import patch

import pytest
from django.core.management import call_command

from datahub.company.test.factories import CompanyFactory
from datahub.company_activity.models import GreatExportEnquiry
from datahub.company_activity.tests.factories import GreatExportEnquiryFactory
from datahub.metadata.models import Country

pytestmark = pytest.mark.django_db


# TODO: Remove file once command has been run as one-off data modification


def test_set_export_enquirer_country(caplog):
    united_kingdom = Country.objects.get(iso_alpha2_code='GB')
    canada = Country.objects.get(iso_alpha2_code='CA')

    # setup enquiries
    company_with_no_address_country = CompanyFactory(address_country_id=None)
    enquiry_with_no_company_address_country = GreatExportEnquiryFactory(
        company=company_with_no_address_country,
    )
    GreatExportEnquiryFactory(company=company_with_no_address_country)
    GreatExportEnquiryFactory(company=CompanyFactory(address_country_id=canada.id))
    GreatExportEnquiryFactory(company=CompanyFactory(address_country_id=united_kingdom.id))

    # initial assertions
    assert enquiry_with_no_company_address_country.company.address_country is None
    assert GreatExportEnquiry.objects.count() == 4
    assert GreatExportEnquiry.objects.filter(company__address_country=united_kingdom).count() == 1

    # execute job
    with caplog.at_level(logging.INFO):
        call_command('set_export_enquirer_country')
        assert (
            'Found 2 GreatExportEnquiry enquiries with no company address country.' in caplog.text
        )
        assert (
            'Found 1 GreatExportEnquiry enquiring companies with no address country.'
            in caplog.text
        )
        assert 'Finished modifying GreatExportEnquiry companies without a country.' in caplog.text

    # final assertions
    enquiry_with_no_company_address_country.refresh_from_db()
    assert enquiry_with_no_company_address_country.company.address_country == united_kingdom
    assert GreatExportEnquiry.objects.count() == 4
    assert GreatExportEnquiry.objects.filter(company__address_country=united_kingdom).count() == 3


def test_set_export_enquirer_country_when_theres_no_projects(caplog):
    with caplog.at_level(logging.INFO):
        call_command('set_export_enquirer_country')
        assert 'No GreatExportEnquiry companies without a country. Exiting...' in caplog.text


@patch('datahub.company_activity.models.GreatExportEnquiry.objects.filter')
def test_set_export_enquirer_country_handles_error(mock_filter, caplog):
    mock_filter.side_effect = Exception('A generic test exception')
    with caplog.at_level(logging.ERROR):
        call_command('set_export_enquirer_country')
        assert (
            'An error occurred trying to modify GreatExportEnquiry companies without a country:'
            in caplog.text
        )
