import datetime


from datahub.core.test_utils import (
    APITestMixin,
)
from datahub.task.emails import (
    TaskAssignedToOthersEmailTemplate,
    TaskCompletedEmailTemplate,
    TaskOverdueEmailTemplate,
    UpcomingTaskEmailTemplate,
)

from datahub.task.test.factories import InvestmentProjectTaskFactory, TaskFactory


class BaseTaskEmailTemplateTests(APITestMixin):
    email_template_class = None

    def test_subject(self):
        task = TaskFactory(due_date=datetime.date.today())
        email = self.email_template_class(task)
        assert email.get_task_subject() == f'{email.subject}: {task.title}'

    def get_investment_project_common_fields(self, investment_project_task):
        return [
            f'Investment project: {investment_project_task.investment_project.name}',
            f'Company name: {investment_project_task.get_company().name}',
            f'Date due: {investment_project_task.task.due_date.strftime("%-d %B %Y")}',
        ]


class TestUpcomingTaskEmailTemplate(BaseTaskEmailTemplateTests):
    email_template_class = UpcomingTaskEmailTemplate

    def test_task_fields_on_investment_project_tasks(self):
        task = InvestmentProjectTaskFactory(task=TaskFactory(due_date=datetime.date.today()))

        email = self.email_template_class(task.task)
        labels = self.get_investment_project_common_fields(task)
        assert email.get_task_fields() == '\n'.join(labels)


class TestTaskAssignedToOthersEmailTemplate(BaseTaskEmailTemplateTests):
    email_template_class = TaskAssignedToOthersEmailTemplate

    def test_task_fields_on_investment_project_tasks(self):
        task = InvestmentProjectTaskFactory(task=TaskFactory(due_date=datetime.date.today()))

        email = self.email_template_class(task.task)
        labels = self.get_investment_project_common_fields(task)
        assert email.get_task_fields() == '\n'.join(labels)


class TestTaskOverdueEmailTemplate(BaseTaskEmailTemplateTests):
    email_template_class = TaskOverdueEmailTemplate

    def test_task_fields_on_investment_project_tasks(self):
        task = InvestmentProjectTaskFactory(task=TaskFactory(due_date=datetime.date.today()))

        email = self.email_template_class(task.task)
        labels = self.get_investment_project_common_fields(task)
        assert email.get_task_fields() == '\n'.join(labels)


class TestTaskCompletedEmailTemplate(BaseTaskEmailTemplateTests):
    email_template_class = TaskCompletedEmailTemplate

    def test_task_fields_on_investment_project_tasks(self):
        task = InvestmentProjectTaskFactory(task=TaskFactory(due_date=datetime.date.today()))

        email = self.email_template_class(task.task)
        labels = self.get_investment_project_common_fields(task) + [
            f'Completed by: {task.task.modified_by.name}',
        ]
        assert email.get_task_fields() == '\n'.join(labels)