import datetime

from pytest import fixture

from datahub.core.test_utils import (
    APITestMixin,
)
from datahub.company.test.factories import CompanyFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.task.emails import (
    TaskAmendedByOthersEmailTemplate,
    TaskAssignedToOthersEmailTemplate,
    TaskCompletedEmailTemplate,
    TaskOverdueEmailTemplate,
    UpcomingTaskEmailTemplate,
)

from datahub.task.test.factories import TaskFactory


@fixture
def generic_task():
    return TaskFactory(
        due_date=datetime.date.today(),
    )


@fixture
def investment_project_task():
    return TaskFactory(
        due_date=datetime.date.today(),
        investment_project=InvestmentProjectFactory(),
    )


@fixture
def company_task():
    return TaskFactory(
        due_date=datetime.date.today(),
        company=CompanyFactory(),
    )


class BaseTaskEmailTemplateTests(APITestMixin):
    def investment_project(self, task):
        return task.investment_project.name

    def due_date(self, task):
        return task.due_date.strftime('%-d %B %Y')

    def company(self, task):
        return task.get_company().name

    email_template_class = None

    default_generic_fields = [('Date due', due_date)]
    additional_generic_fields = []

    default_investment_project_fields = [
        ('Investment project', investment_project),
        ('Company name', company),
        ('Date due', due_date),
    ]
    additional_investment_project_fields = []

    default_company_fields = [('Company name', company), ('Date due', due_date)]
    additional_company_fields = []

    def test_subject(self):
        task = TaskFactory(due_date=datetime.date.today())
        email = self.email_template_class(task)
        assert email.get_task_subject() == f'{email.subject}: {task.title}'

    def test_generic_email_fields(self, generic_task):
        email = self.email_template_class(generic_task)

        labels = [
            f'{field[0]}: {field[1](self, task=generic_task)}'
            for field in self.default_generic_fields + self.additional_generic_fields
        ]
        assert email.get_task_fields() == '\n'.join(labels)

    def test_investment_project_email_fields(self, investment_project_task):
        email = self.email_template_class(investment_project_task)
        labels = [
            f'{field[0]}: {field[1](self, task=investment_project_task)}'
            for field in self.default_investment_project_fields
            + self.additional_investment_project_fields
        ]
        assert email.get_task_fields() == '\n'.join(labels)

    def test_company_email_fields(self, company_task):
        email = self.email_template_class(company_task)
        labels = [
            f'{field[0]}: {field[1](self, task=company_task)}'
            for field in self.default_company_fields + self.additional_company_fields
        ]
        assert email.get_task_fields() == '\n'.join(labels)


class TestUpcomingTaskEmailTemplate(BaseTaskEmailTemplateTests):
    email_template_class = UpcomingTaskEmailTemplate


class TestTaskAssignedToOthersEmailTemplate(BaseTaskEmailTemplateTests):
    email_template_class = TaskAssignedToOthersEmailTemplate


class TestTaskOverdueEmailTemplate(BaseTaskEmailTemplateTests):
    email_template_class = TaskOverdueEmailTemplate


class TestTaskCompletedEmailTemplate(BaseTaskEmailTemplateTests):
    email_template_class = TaskCompletedEmailTemplate

    def completed_by(self, task):
        return task.modified_by.name

    additional_generic_fields = [('Completed by', completed_by)]
    additional_investment_project_fields = [('Completed by', completed_by)]
    additional_company_fields = [('Completed by', completed_by)]


class TestTaskAmendedByOthersEmailTemplate(BaseTaskEmailTemplateTests):
    email_template_class = TaskAmendedByOthersEmailTemplate

    def amended_by(self, task):
        return task.modified_by.name

    additional_generic_fields = [('Amended by', amended_by)]
    additional_investment_project_fields = [('Amended by', amended_by)]
    additional_company_fields = [('Amended by', amended_by)]
