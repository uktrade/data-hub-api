import random

import factory.fuzzy

from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory
from datahub.core.test.factories import to_many_field
from datahub.task.models import Task


class TaskFactory(factory.django.DjangoModelFactory):
    """Factory for creating tasks"""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    created_on = now()
    title = factory.Faker('company')
    investment_project = None

    archived = False

    @to_many_field
    def advisers(self):
        """
        Add support for setting `advisers`.
        """
        return AdviserFactory.create_batch(random.randint(1, 3))

    class Meta:
        model = Task
