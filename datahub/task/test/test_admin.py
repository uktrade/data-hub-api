import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.task.admin import TaskAdminForm


from datahub.investment.project.test.factories import InvestmentProjectFactory


pytestmark = pytest.mark.django_db


class TestTaskAdminModel:
    def test_admin_form_throws_validation_error_when_task_has_company_and_investment_project(
        self,
    ):
        data = {
            'company': CompanyFactory().id,
            'investment_project': InvestmentProjectFactory().id,
        }
        form = TaskAdminForm(data=data)

        assert form.is_valid() is False
        assert form.non_field_errors() == [
            'You cannot assign both a company and investment project to a task',
        ]
