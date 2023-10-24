import random

import factory.fuzzy
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory
from datahub.core.test.factories import to_many_field
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.task.models import InvestmentProjectTask, Task


class TaskFactory(factory.django.DjangoModelFactory):
    """Factory for creating tasks"""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    created_on = now()
    title = factory.Faker('company')

    archived = False

    @to_many_field
    def advisers(self):
        """
        Add support for setting `advisers`.
        """
        return AdviserFactory.create_batch(random.randint(1, 3))

    class Meta:
        model = Task


class InvestmentProjectTaskFactory(factory.django.DjangoModelFactory):
    """Factory for creating investment project tasks"""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    created_on = now()

    task = factory.SubFactory(TaskFactory)
    investment_project = factory.SubFactory(InvestmentProjectFactory)

    class Meta:
        model = InvestmentProjectTask
