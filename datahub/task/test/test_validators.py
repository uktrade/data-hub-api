import pytest

from django.core.exceptions import ValidationError

from datahub.company.test.factories import CompanyFactory

from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.task.validators import validate_single_task_relationship


pytestmark = [pytest.mark.django_db]


def test_validate_task_does_not_throw_error_when_company_and_investment_project_none():
    validate_single_task_relationship(
        None,
        None,
        ValidationError,
    )


def test_validate_task_does_not_throw_error_when_company_none():
    validate_single_task_relationship(
        InvestmentProjectFactory(),
        None,
        ValidationError,
    )


def test_validate_task_does_not_throw_error_when_investment_project_none():
    validate_single_task_relationship(
        None,
        CompanyFactory(),
        ValidationError,
    )


def test_validate_task_throws_error_when_company_and_investment_project_exist():
    with pytest.raises(ValidationError):
        validate_single_task_relationship(
            InvestmentProjectFactory(),
            CompanyFactory(),
            ValidationError,
        )
