import pytest

from datahub.company.validators import (
    has_no_invalid_company_number_characters,
    has_uk_establishment_number_prefix,
)


@pytest.mark.parametrize('company_number,is_valid', (
    ('BR000555', True),
    ('BR000555%^', False),
    ('BR000555é', False),
    ('br000555', False),
    ('BR000555 ', False),
))
def test_has_no_invalid_company_number_characters(company_number, is_valid):
    """Tests validation of company number characters."""
    assert has_no_invalid_company_number_characters(company_number) == is_valid


@pytest.mark.parametrize('company_number,is_valid', (
    ('BR000555', True),
    ('SC000555', False),
    ('br000555', False),
))
def test_has_uk_establishment_number_prefix(company_number, is_valid):
    """Tests validation of UK establishment prefix."""
    assert has_uk_establishment_number_prefix(company_number) == is_valid
