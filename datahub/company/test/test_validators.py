import pytest

from datahub.company.validators import (
    has_no_invalid_company_number_characters,
    has_team_member_count_exceeded_max_allowed,
    has_uk_establishment_number_prefix,
)


@pytest.mark.parametrize(
    'company_number,is_valid',
    (
        ('BR000555', True),
        ('BR000555%^', False),
        ('BR000555é', False),
        ('br000555', False),
        ('BR000555 ', False),
    ),
)
def test_has_no_invalid_company_number_characters(company_number, is_valid):
    """Tests validation of company number characters."""
    assert has_no_invalid_company_number_characters(company_number) == is_valid


@pytest.mark.parametrize(
    'company_number,is_valid',
    (
        ('BR000555', True),
        ('SC000555', False),
        ('br000555', False),
    ),
)
def test_has_uk_establishment_number_prefix(company_number, is_valid):
    """Tests validation of UK establishment prefix."""
    assert has_uk_establishment_number_prefix(company_number) == is_valid


def test_has_team_member_count_exceeded_max_allowed_returns_false_when_team_members_is_none():
    assert has_team_member_count_exceeded_max_allowed(None) is False


@pytest.mark.parametrize('size', (0, 2, 5))
def test_has_team_member_count_exceeded_max_allowed_returns_false_when_team_members_below_max(
    size,
):
    assert has_team_member_count_exceeded_max_allowed(['a'] * size) is False


@pytest.mark.parametrize('size', (6, 10))
def test_has_team_member_count_exceeded_max_allowed_returns_true_when_team_members_exceed_max(
    size,
):
    assert has_team_member_count_exceeded_max_allowed(['a'] * size) is True
