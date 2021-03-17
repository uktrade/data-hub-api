import re

import pytest
from django.core.management import call_command

from datahub.company.models import Company
from datahub.company.test.factories import USCompanyFactory
from datahub. \
    dbmaintenance. \
    management. \
    commands. \
    fix_us_company_address_postcode_for_company_address_area import Command

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('post_code, expected_result',
                         [('1 0402', '10402'),
                          ('123456789', '123456789'),
                          ('8520 7402', '07402'),
                          ('CA90025', '90025'),
                          ('NY 10174 – 4099', '10174 – 4099'),
                          ('NY 10174 - 4099', '10174 - 4099'),
                          ('MC 5270 3800', '03800'),
                          ('A1B 4H7', 'A1B 4H7'),
                          ('K1C1T1', 'K1C1T1'),
                          ('NY 1004', 'NY 1004'),
                          ('YO22 4PT', 'YO22 4PT'),
                          ('RH175NB', 'RH175NB'),
                          ('MA 02 111', 'MA 02 111'),
                          ('PO Box 2900', 'PO Box 2900'),
                          ('WA 6155', 'WA 6155'),
                          ('BT12 6RE', 'BT12 6RE'),
                          ('5 Westheimer Road', '5 Westheimer Road'),
                          ('M2 4JB', 'M2 4JB'),
                          ('CA USA', 'CA USA'),
                          ('NA', 'NA'),
                          ('n/a', 'n/a'),
                          ('MN5512', 'MN5512'),
                          ('BB12 7DY', 'BB12 7DY'),
                          ('PO6 3EZ', 'PO6 3EZ'),
                          ('Nw1 2Ew', 'Nw1 2Ew'),
                          ('WC1R 5NR', 'WC1R 5NR'),
                          ('VA 2210', 'VA 2210'),
                          ('BH12 4NU', 'BH12 4NU'),
                          ('tbc', 'tbc'),
                          ('CT 6506', 'CT 6506'),
                          ('ME9 0NA', 'ME9 0NA'),
                          ('DY14 0QU', 'DY14 0QU'),
                          ('12345', '12345'),
                          ('12345-1234', '12345-1234'),
                          ('12345 - 1234', '12345 - 1234'),
                          ('0 12345', '01234'),
                          ])
def test_command_regex_generates_the_expected_postcode_substitution(post_code, expected_result):
    """
    Test regex efficiently without connecting to a database
    @param post_code: POSTCODE format good and bad
    @param expected_result: regular expression substituted value using the
           Command pattern
    """
    actual_result = re.sub(
        Command.POST_CODE_PATTERN,
        Command.REPLACEMENT,
        post_code,
        0,
        re.MULTILINE)
    assert actual_result == expected_result


@pytest.mark.parametrize('post_code, area_code, area_name',
                         [('00589', 'NY', 'New York'),
                          ('00612-1234', 'PR', 'Puerto Rico'),
                          ('01012', 'MA', 'Massachusetts'),
                          ('02823', 'RI', 'Rhode Island'),
                          ('030121234', 'NH', 'New Hampshire'),
                          ('03912', 'ME', 'Maine'),
                          ('04946', 'ME', 'Maine'),
                          ('05067-1234', 'VT', 'Vermont'),
                          ])
def test_us_company_with_unique_zips_generates_valid_address_area(
        post_code,
        area_code,
        area_name):
    """
    Test postcode fixes and area generation a couple of valid Zip Codes using the real DB
    @param post_code: POSTCODE good
    @param area_code: Area Code to be generated from Command
    @param area_name: Area Name to describe area code
    """
    company = USCompanyFactory.create(
        address_postcode=post_code,
        registered_address_postcode=post_code,
    )
    assert company.address_area is None

    call_command('fix_us_company_address_postcode_for_company_address_area')

    current_company = Company.objects.first()
    assert current_company.address_area is not None
    assert current_company.address_area.area_code == area_code
    assert current_company.address_postcode == post_code


@pytest.mark.parametrize('post_code, area_code, area_name', [
    ('05512', 'MA', 'Massachusetts'),
    ('05612-1234', 'VT', 'Vermont'),
    ('060123456', 'CT', 'Connecticut'),
    ('07045', 'NJ', 'New Jersey'),
    ('10057', 'NY', 'New York'),
    ('15078', 'PA', 'Pennsylvania'),
    ('19789-4567', 'DE', 'Delaware'),
    ('20067', 'DC', 'District of Columbia'),
])
def test_us_company_with_unique_zips_generates_the_valid_registered_address_area(
        post_code,
        area_code,
        area_name):
    """
    Test registered address postcode fixes and area generation a
    couple of valid Zip Codes using the real DB
    @param post_code: POSTCODE good
    @param area_code: Area Code to be generated from Command
    @param area_name: Area Name to describe area code
    """
    company = USCompanyFactory.create(
        address_postcode=post_code,
        registered_address_postcode=post_code,
    )
    assert company.registered_address_area is None

    call_command('fix_us_company_address_postcode_for_company_address_area')

    current_company = Company.objects.first()
    assert current_company.registered_address_area is not None
    assert current_company.registered_address_area.area_code == area_code
    assert current_company.registered_address_postcode == post_code


@pytest.mark.parametrize('post_code, expected_result',
                         [('1 0402', '10402'),
                          ('8520 7402', '07402'),
                          ('CA90025', '90025'),
                          ('NY 10174 – 4099', '10174 – 4099'),
                          ('NY 10174 - 4099', '10174 - 4099'),
                          ('NY 123456789', '123456789'),
                          ])
def test_command_fixes_invalid_postcodes_in_all_post_code_fields(
        post_code,
        expected_result):
    """
    Test Patterns that need fixing in all postcode fields
    @param post_code: Invalid Postcode Format
    @param expected_result:  The expected result of the fix
    """
    company = USCompanyFactory.create(
        address_postcode=post_code,
        registered_address_postcode=post_code,
    )
    assert company.address_postcode == post_code
    assert company.registered_address_postcode == post_code

    call_command('fix_us_company_address_postcode_for_company_address_area')

    current_company = Company.objects.first()
    assert current_company.address_postcode == expected_result
    assert current_company.registered_address_postcode == expected_result
