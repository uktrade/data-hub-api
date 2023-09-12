import factory.fuzzy
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory
from datahub.core.test.factories import to_many_field
from datahub.task.models import InvestmentProjectTask, Task


class TaskFactory(factory.django.DjangoModelFactory):
    """Factory for creating tasks"""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    created_on = now()

    archived = False

    @to_many_field
    def advisers(self):  # noqa: D102
        """
        Add support for setting `advisers`.
        """
        return []

    class Meta:
        model = Task


class InvestmentProjectTaskFactory(factory.django.DjangoModelFactory):
    """Factory for creating investment project tasks"""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    created_on = now()

    class Meta:
        model = InvestmentProjectTask
