from abc import ABC, abstractmethod
from typing import List

from datahub.task.models import Task


class EmailTemplate(ABC):
    @abstractmethod
    def __init__(self, task: Task):
        self.task = task

    @property
    @abstractmethod
    def subject(self) -> str:
        pass

    @property
    @abstractmethod
    def fields_to_include(self) -> List[str]:
        pass

    @property
    def company_name(self):
        return (
            f'Company name: {self.task.get_company().name }' if self.task.get_company() else None
        )

    @property
    def investment_project(self):
        return (
            f'Investment project: {self.task.investment_project.name}'
            if self.task.investment_project
            else None
        )

    @property
    def adviser_completing_task(self):
        return f'Completed by: {self.task.modified_by.name}'

    @property
    def adviser_amending_task(self):
        return f'Amended by: {self.task.modified_by.name}'

    @property
    def task_due_date(self):
        return (
            f'Date due: {self.task.due_date.strftime("%-d %B %Y")}' if self.task.due_date else None
        )

    def get_task_fields(self) -> str:
        """Return a list of all the fields to include, separated by new line"""
        return '\n'.join(list(filter(lambda item: item is not None, self.fields_to_include)))

    def get_task_subject(self) -> str:
        return f'{self.subject}: {self.task.title}'

    def get_body_heading(self) -> str:
        return f'{self.subject}: {self.task.title}'

    def get_context(self):
        return {
            'email_subject': self.get_task_subject(),
            'body_heading': self.get_body_heading(),
            'task_fields': self.get_task_fields(),
            'task_url': self.task.get_absolute_url(),
        }


class UpcomingTaskEmailTemplate(EmailTemplate):
    def __init__(self, task: Task):
        super().__init__(task)

    @property
    def subject(self):
        return f'Your task is due in {self.task.reminder_days} days'

    @property
    def fields_to_include(self):
        return [
            self.investment_project,
            self.company_name,
            self.task_due_date,
        ]


class TaskOverdueEmailTemplate(EmailTemplate):
    def __init__(self, task: Task):
        super().__init__(task)

    @property
    def subject(self):
        return 'Your task is now overdue'

    @property
    def fields_to_include(self):
        return [
            self.investment_project,
            self.company_name,
            self.task_due_date,
        ]


class TaskAssignedToOthersEmailTemplate(EmailTemplate):
    def __init__(self, task: Task):
        super().__init__(task)

    @property
    def subject(self):
        return 'You have been assigned to task'

    @property
    def fields_to_include(self):
        return [
            self.investment_project,
            self.company_name,
            self.task_due_date,
        ]


class TaskCompletedEmailTemplate(EmailTemplate):
    def __init__(self, task: Task):
        super().__init__(task)

    @property
    def subject(self):
        return 'Task completed'

    @property
    def fields_to_include(self):
        return [
            self.investment_project,
            self.company_name,
            self.task_due_date,
            self.adviser_completing_task,
        ]


class TaskAmendedByOthersEmailTemplate(EmailTemplate):
    def __init__(self, task: Task):
        super().__init__(task)

    @property
    def subject(self):
        return 'Task amended'

    @property
    def fields_to_include(self):
        return [
            self.investment_project,
            self.company_name,
            self.task_due_date,
            self.adviser_amending_task,
        ]
