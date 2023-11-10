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

    def get_all_fields(self):
        return {
            'company_name': (
                (
                    'Company name',
                    self.task.get_company().name if self.task.get_company() else None,
                )
            ),
            'investment_project': (
                (
                    'Investment project',
                    self.task.task_investmentprojecttask.investment_project.name
                    if hasattr(self.task, 'task_investmentprojecttask')
                    else None,
                )
            ),
            'task_due_date': (
                (
                    'Date due',
                    self.task.due_date.strftime('%-d %B %Y'),
                )
            ),
        }

    def get_task_fields(self) -> str:
        """Return a list of all the fields to include, separated by new line"""
        all_fields = self.get_all_fields()
        field_labels = []
        for field_to_include in self.fields_to_include:
            found_field = all_fields[field_to_include]
            if found_field[1]:
                field_labels.append(f'{found_field[0]}: {found_field[1]}')

        return '\n'.join(field_labels)

    def get_task_subject(self) -> str:
        print(self.task)
        return f'{self.subject}: {self.task.title}'

    def get_context(self):
        print(self)
        print(self.task)
        return {
            'email_subject': self.get_task_subject(),
            'body_heading': f'{self.subject}: {self.task.title}',
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
    def fields_to_include(self) -> List[str]:
        return ['investment_project', 'company_name', 'task_due_date']


class TaskOverdueEmailTemplate(EmailTemplate):
    def __init__(self, task):
        super().__init__(task)

    @property
    def subject(self):
        return 'Your task is now overdue'

    @property
    def fields_to_include(self) -> List[str]:
        return ['investment_project', 'company_name', 'task_due_date']


class TaskAssignedToOthersEmailTemplate(EmailTemplate):
    def __init__(self, task: Task):
        super().__init__(task)

    @property
    def subject(self):
        return 'You have been assigned to task'

    @property
    def fields_to_include(self) -> List[str]:
        return ['investment_project', 'company_name', 'task_due_date']
