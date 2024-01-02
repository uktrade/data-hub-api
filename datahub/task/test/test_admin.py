from datahub.interaction.test.factories import InteractionFactoryBase
import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.task.admin import TaskAdminForm


pytestmark = pytest.mark.django_db


class TestTaskAdminModel:
    def test_admin_form_validation_error_when_task_has_company__investment_project__interaction(
        self,
    ):
        data = {
            'company': CompanyFactory().id,
            'investment_project': InvestmentProjectFactory().id,
            'interaction': InteractionFactoryBase().id,
        }
        form = TaskAdminForm(data=data)

        assert form.is_valid() is False
        assert form.non_field_errors() == [
            'You can assign either a company, investment project or interaction to a task',
        ]
