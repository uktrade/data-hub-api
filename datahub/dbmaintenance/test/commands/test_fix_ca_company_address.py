import pytest
from django.core.management import call_command

from datahub.company.test.factories import CompanyFactory
from datahub.core.constants import Country
from datahub.core.postcode_constants import CountryPostcodeReplacement
from datahub.core.test_utils import has_reversion_comment, has_reversion_version
from datahub.dbmaintenance.resolvers.company_address import CompanyAddressResolver

pytestmark = pytest.mark.django_db


def setup_ca_company_with_all_addresses(post_code):
    """Sets up CA Company for tests"""
    return CompanyFactory(
        address_town='Saskatoon',
        address_country_id=Country.canada.value.id,
        address_postcode=post_code,
        address_area_id=None,
        registered_address_town='Saskatoon',
        registered_address_country_id=Country.canada.value.id,
        registered_address_postcode=post_code,
        registered_address_area_id=None,
        uk_region_id=None,
        archived=False,
        duns_number='123456789',
    )


def setup_ca_company_with_address_only(post_code):
    """Sets up Canada Company with address only for tests"""
    return CompanyFactory(
        address_town='Saskatoon',
        address_country_id=Country.canada.value.id,
        address_postcode=post_code,
        address_area_id=None,
        registered_address_town='',
        registered_address_country_id=None,
        registered_address_postcode='',
        registered_address_area_id=None,
        uk_region_id=None,
        archived=False,
        duns_number='123456789',
    )


def setup_ca_company_with_registered_address_only(post_code):
    """Sets up Canada Company with registered address only for tests"""
    return CompanyFactory(
        registered_address_town='Saskatoon',
        registered_address_country_id=Country.canada.value.id,
        registered_address_postcode=post_code,
        registered_address_area_id=None,
        address_town='',
        address_country_id=None,
        address_postcode='',
        address_area_id=None,
        uk_region_id=None,
        archived=False,
        duns_number='123456789',
    )


@pytest.mark.parametrize(
    'post_code, expected_result',
    [
        ('M5H 2M5', 'M5H 2M5'),
        ('v6c 0c3', 'v6c 0c3'),
        ('H3Z-217', 'H3Z-217'),
        ('none provided', 'none provided'),
        ('N2H', 'N2H'),
        ('T6h5H6', 'T6h5H6'),
        ('M5V 1K4', 'M5V 1K4'),
        ('R3H 1B5', 'R3H 1B5'),
        ('ON  L2A 3T9', 'L2A 3T9'),
        ('ONM5H3M7', 'M5H3M7'),
        ('m5m e7u', 'm5m e7u'),
        ('6120', '6120'),
        ('77040', '77040'),
        ('ON L4V 1T4', 'L4V 1T4'),
        ('0', '0'),
        ('Unknown', 'Unknown'),
        ('k7m 8s3', 'k7m 8s3'),
        ('V6H 4A7', 'V6H 4A7'),
        ('BC V8W 1A7', 'V8W 1A7'),
        ('L9H-1V1', 'L9H-1V1'),
        ('N/A', 'N/A'),
        ('139 Mulock Avenue', '139 Mulock Avenue'),
        ('ON L1S 3A2', 'L1S 3A2'),
        ('Kanata', 'Kanata'),
        ('LAVAL', 'LAVAL'),
        ('T"R 0E3', 'T"R 0E3'),
        ('Ohio 44130', 'Ohio 44130'),
        ('VA 22180', 'VA 22180'),
        ('Nb E3B 217', 'Nb E3B 217'),
        ('PO Box 370', 'PO Box 370'),
        ('oooooo', 'oooooo'),
    ],
)
def test_command_regex_generates_the_expected_postcode_substitution(
    post_code,
    expected_result,
):
    """
    Test regex efficiently without connecting to a database
    :param post_code: POSTCODE format good and bad
    :param expected_result: regular expression substituted value using the
           Command pattern
    """
    resolver = CompanyAddressResolver(
        country_id=None,
        revision_comment=None,
        zip_states=None,
        postcode_replacement=CountryPostcodeReplacement.canada.value,
    )
    actual_result = resolver.format_postcode(post_code)
    assert actual_result == expected_result


@pytest.mark.parametrize(
    'post_code, area_code',
    [
        ('J2W 4C0', 'QC'),
        ('P2A6K7', 'ON'),
        ('J5J-4M5', 'QC'),
        ('V8B 1T6', 'BC'),
    ],
)
def test_ca_company_with_unique_zips_generates_valid_address_area(
    post_code,
    area_code,
):
    """
    Test postcode is fixed for the purpose of admin area
    generation with valid zip codes format
    :param post_code: POSTCODE good
    :param area_code: Area Code to be generated from Command
    """
    company = setup_ca_company_with_all_addresses(post_code)
    assert company.address_area is None

    call_command('fix_ca_company_address')

    company.refresh_from_db()
    assert company.address_area is not None
    assert company.address_area.area_code == area_code
    assert company.address_postcode == post_code


@pytest.mark.parametrize(
    'post_code, area_code',
    [
        ('T8L 3X6', 'AB'),
        ('B2J-6A2', 'NS'),
        ('E6B2H0', 'NB'),
        ('A1V 2E1', 'NL'),
    ],
)
def test_ca_company_with_address_data_only_will_generate_address_area(
    post_code,
    area_code,
):
    """
    Test postcode fixes and area generation with address area data
    :param post_code: POSTCODE good
    :param area_code: Area Code to be generated from Command
    """
    company = setup_ca_company_with_address_only(post_code)
    assert company.address_area is None

    call_command('fix_ca_company_address')

    company.refresh_from_db()
    assert company.address_area is not None
    assert company.address_area.area_code == area_code
    assert company.address_postcode == post_code


@pytest.mark.parametrize(
    'post_code, area_code',
    [
        ('E3L 3E2', 'NB'),
        ('R2C 1V3', 'MB'),
        ('S9V 5S7', 'SK'),
        ('A2N 6S1', 'NL'),
    ],
)
def test_ca_company_with_unique_zips_generates_the_valid_registered_address_area(
    post_code,
    area_code,
):
    """
    Test registered address postcode fixes and area generation a
    couple of valid Zip Codes using the real DB
    :param post_code: POSTCODE good
    :param area_code: Area Code to be generated from Command
    """
    company = setup_ca_company_with_all_addresses(post_code)
    assert company.registered_address_area is None

    call_command('fix_ca_company_address')

    company.refresh_from_db()
    assert company.registered_address_area is not None
    assert company.registered_address_area.area_code == area_code
    assert company.registered_address_postcode == post_code


@pytest.mark.parametrize(
    'post_code, area_code',
    [
        ('T8L 3B8', 'AB'),
        ('C0A 1S7', 'PE'),
        ('V8A 9N4', 'BC'),
        ('A5A 0H7', 'NL'),
    ],
)
def test_ca_company_with_registered_address_data_only_will_generate_registered_address_area(
    post_code,
    area_code,
):
    """
    Test registered address data only creates data expected
    :param post_code: POSTCODE good
    :param area_code: Area Code to be generated from Command
    """
    company = setup_ca_company_with_registered_address_only(post_code)
    assert company.registered_address_area is None

    call_command('fix_ca_company_address')

    company.refresh_from_db()
    assert company.registered_address_area is not None
    assert company.registered_address_area.area_code == area_code
    assert company.registered_address_postcode == post_code


@pytest.mark.parametrize(
    'post_code, expected_result',
    [
        ('ON  L2A 3T9', 'L2A 3T9'),
        ('AB T4N 6M4', 'T4N 6M4'),
        ('ONM5H3M7', 'M5H3M7'),
        ('BC V8W 1A7', 'V8W 1A7'),
        ('ON L1S 3A2', 'L1S 3A2'),
        ('NB E1E 2C6', 'E1E 2C6'),
        ('Qc J4Y 0L2', 'J4Y 0L2'),
    ],
)
def test_command_fixes_invalid_postcodes_in_all_post_code_fields(
    post_code,
    expected_result,
):
    """
    Test Patterns that need fixing in all postcode fields
    :param post_code: Invalid Postcode Format
    :param expected_result:  The expected result of the fix
    """
    company = setup_ca_company_with_all_addresses(post_code)
    assert company.address_postcode == post_code
    assert company.registered_address_postcode == post_code

    call_command('fix_ca_company_address')

    company.refresh_from_db()
    assert company.address_postcode == expected_result
    assert company.registered_address_postcode == expected_result


@pytest.mark.parametrize(
    'post_code, expected_result',
    [
        ('T"R 0E3', 'T"R 0E3'),
        ('Ohio 44130', 'Ohio 44130'),
        ('VA 22180', 'VA 22180'),
        ('Nb E3B 217', 'Nb E3B 217'),
        ('PO Box 370', 'PO Box 370'),
        ('oooooo', 'oooooo'),
    ],
)
def test_command_leaves_invalid_postcodes_in_original_state_with_no_area(
    post_code,
    expected_result,
):
    """
    Test edge cases are preserved
    :param post_code: Invalid Postcode Format
    :param expected_result:  The expected result of the fix
    """
    company = setup_ca_company_with_all_addresses(post_code)

    call_command('fix_ca_company_address')

    company.refresh_from_db()
    assert company.address_postcode == expected_result
    assert company.registered_address_postcode == expected_result
    assert company.address_area is None
    assert company.registered_address_area is None


@pytest.mark.parametrize(
    'post_code, expected_result',
    [
        ('E3L 3E2', 'E3L 3E2'),
        ('R2C-1V3', 'R2C-1V3'),
        ('S9V5S7', 'S9V5S7'),
    ],
)
def test_audit_log(post_code, expected_result):
    """
    Verify auditable versions of the code are retained
    :param post_code: Invalid Postcode Format
    :param expected_result:  The expected result of the fix
    """
    company = setup_ca_company_with_all_addresses(post_code)

    call_command('fix_ca_company_address')

    company.refresh_from_db()
    assert company.address_postcode == expected_result
    assert company.registered_address_postcode == expected_result
    assert has_reversion_version(company)
    assert has_reversion_comment('Canada area and postcode fix.')


@pytest.mark.parametrize(
    'post_code, expected_result',
    [
        ('E3L 3E2', 'E3L 3E2'),
        ('R2C-1V3', 'R2C-1V3'),
        ('S9V5S7', 'S9V5S7'),
    ],
)
def test_audit_does_not_continue_creating_revisions(post_code, expected_result):
    """
    Verify auditable versions of the code are retained
    :param post_code: Invalid Postcode Format
    :param expected_result:  The expected result of the fix
    """
    company = setup_ca_company_with_all_addresses(post_code)

    call_command('fix_ca_company_address')
    company.refresh_from_db()

    assert has_reversion_version(company, 1)
    assert company.address_postcode == expected_result
    assert company.registered_address_postcode == expected_result

    call_command('fix_ca_company_address')
    company.refresh_from_db()

    assert has_reversion_version(company, 1)
    assert company.address_postcode == expected_result
    assert company.registered_address_postcode == expected_result
