import pytest
from django.core.exceptions import ValidationError

from datahub.company.validators import (
    has_no_invalid_company_number_characters,
    has_uk_establishment_number_prefix,
    validate_team_member_max_count,
)


@pytest.mark.parametrize(
    ('company_number', 'is_valid'),
    [
        ('BR000555', True),
        ('BR000555%^', False),
        ('BR000555é', False),
        ('br000555', False),
        ('BR000555 ', False),
    ],
)
def test_has_no_invalid_company_number_characters(company_number, is_valid):
    """Tests validation of company number characters."""
    assert has_no_invalid_company_number_characters(company_number) == is_valid


@pytest.mark.parametrize(
    ('company_number', 'is_valid'),
    [
        ('BR000555', True),
        ('SC000555', False),
        ('br000555', False),
    ],
)
def test_has_uk_establishment_number_prefix(company_number, is_valid):
    """Tests validation of UK establishment prefix."""
    assert has_uk_establishment_number_prefix(company_number) == is_valid


def test_validate_team_member_max_count_does_not_throw_error_when_team_members_is_none():
    """Test no error is thrown when the team_member value is None."""
    validate_team_member_max_count(None, ValidationError)


@pytest.mark.parametrize('size', [0, 2, 5])
def test_validate_team_member_max_count_does_not_throw_error_when_team_members_below_max(
    size,
):
    """Test no error is thrown when the team_member value contains less than the maximum allowed."""
    validate_team_member_max_count(['a'] * size, ValidationError)


@pytest.mark.parametrize('size', [6, 10])
def test_validate_team_member_max_count_throws_error_when_team_members_exceed_max(
    size,
):
    """Test an error is thrown that matches the type of exception provided, when the team_member
    value contains more than the maximum allowed.
    """
    with pytest.raises(ValidationError, match='You can only add 5 team members'):
        validate_team_member_max_count(['a'] * size, ValidationError)


@pytest.mark.parametrize('size', [6, 10])
def test_validate_team_member_max_count_thrown_error_is_wrapped(
    size,
):
    """Test an error is thrown that matches the type of exception provided, when the team_member
    value contains more than the maximum allowed. Test the message of the error is wrapped in an
    object that matches the {wrapper_obj_name} argument.
    """
    with pytest.raises(ValidationError) as excinfo:
        validate_team_member_max_count(['a'] * size, ValidationError, wrapper_obj_name='error')
    assert dict(excinfo.value)['error'] == ['You can only add 5 team members']
