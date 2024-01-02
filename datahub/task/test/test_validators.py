from datahub.interaction.test.factories import InteractionFactoryBase
import pytest

from django.core.exceptions import ValidationError

from datahub.company.test.factories import CompanyFactory

from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.task.validators import validate_single_task_relationship


pytestmark = [pytest.mark.django_db]


def test_validate_task_does_not_throw_error_when_company__investment_project__interaction_none():
    validate_single_task_relationship(
        None,
        None,
        None,
        ValidationError,
    )


def test_validate_task_does_not_throw_error_when_only_company():
    validate_single_task_relationship(
        None,
        CompanyFactory,
        None,
        ValidationError,
    )


def test_validate_task_does_not_throw_error_when_only_investment_project():
    validate_single_task_relationship(
        InvestmentProjectFactory,
        None,
        None,
        ValidationError,
    )


def test_validate_task_does_not_throw_error_when_only_interaction():
    validate_single_task_relationship(
        None,
        None,
        InteractionFactoryBase(),
        ValidationError,
    )


def test_validate_task_throws_error_when_company_and_investment_project_and_interaction_exist():
    with pytest.raises(ValidationError):
        validate_single_task_relationship(
            InvestmentProjectFactory(),
            CompanyFactory(),
            InteractionFactoryBase(),
            ValidationError,
        )
