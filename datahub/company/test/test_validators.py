from unittest.mock import Mock

import pytest

from datahub.company.validators import (
    has_no_invalid_company_number_characters,
    has_uk_establishment_number_prefix,
    is_company_a_global_headquarters,
)
from datahub.core.constants import HeadquarterType


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


@pytest.mark.parametrize('company,is_valid', (
    (None, False),
    (Mock(headquarter_type=Mock(id=HeadquarterType.ehq.value.id)), False),
    (Mock(headquarter_type=Mock(id=HeadquarterType.ukhq.value.id)), False),
    (Mock(headquarter_type=None), False),
    (Mock(headquarter_type=Mock(id=HeadquarterType.ghq.value.id)), True),
))
def test_is_company_a_global_headquarters(company, is_valid):
    """Tests validation of Global Headquarters."""
    assert is_company_a_global_headquarters(company) == is_valid
