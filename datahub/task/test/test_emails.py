import datetime


from datahub.core.test_utils import (
    APITestMixin,
)
from datahub.task.emails import (
    TaskAssignedToOthersEmailTemplate,
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

    def test_task_fields_on_generic_tasks(self):
        task = TaskFactory(due_date=datetime.date.today())
        email = self.email_template_class(task)
        assert email.get_task_fields() == f'Date due: {task.due_date.strftime("%-d %B %Y")}'

    def test_task_fields_on_investment_project_tasks(self):
        task = InvestmentProjectTaskFactory(task=TaskFactory(due_date=datetime.date.today()))

        email = self.email_template_class(task.task)
        labels = [
            f'Investment project: {task.investment_project.name}',
            f'Company name: {task.get_company().name}',
            f'Date due: {task.task.due_date.strftime("%-d %B %Y")}',
        ]
        assert email.get_task_fields() == '\n'.join(labels)


class TestUpcomingTaskEmailTemplate(BaseTaskEmailTemplateTests):
    email_template_class = UpcomingTaskEmailTemplate


class TestTaskAssignedToOthersEmailTemplate(BaseTaskEmailTemplateTests):
    email_template_class = TaskAssignedToOthersEmailTemplate


class TestTaskOverdueEmailTemplate(BaseTaskEmailTemplateTests):
    email_template_class = TaskOverdueEmailTemplate
