import datetime

import pytest

from datahub.task.tasks import generate_reminders_upcoming_tasks
from datahub.task.test.factories import InvestmentProjectTaskFactory, TaskFactory


def invstment_project_factory_due_today(days=1):
    return InvestmentProjectTaskFactory(
        task=TaskFactory(
            due_date=datetime.date.today() + datetime.timedelta(days=days),
            reminder_days=days,
        ),
    )


@pytest.mark.django_db
class TestTaskReminders:
    def test_generate_reminders_for_upcoming_tasks(self):
        # create a few tasks without due reminders
        # create a few tasks with due reminders
        tasks = InvestmentProjectTaskFactory.create_batch(3)
        tasks_due = []
        tasks_due.append(invstment_project_factory_due_today(1))
        tasks_due.append(invstment_project_factory_due_today(7))
        tasks_due.append(invstment_project_factory_due_today(30))
        # task_id = task.id

        # investment_project_task = InvestmentProjectTaskFactory(task=task)

        tasks = generate_reminders_upcoming_tasks()

        # Check tasks count is number due reminders expected
        assert tasks.count() == 1

    # tasks [due_date - reminder_days = today]
    #   advisers [is_active && ]
    #       upcoming_task_reminder_subscription [select email_reminder_enabled]

    #   userfeatureflag or userfeatureflag group set

    # Add reminder to DataHub reminders
    # Send email if upcoming_task_reminder_subscription.email_reminder_enabled
