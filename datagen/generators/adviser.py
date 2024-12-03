from django.db import transaction

from datahub.company.test.factories import AdviserFactory
from datahub.metadata.models import Team


from ..utils import (
    print_progress,
    random_object_from_queryset,
)


def generate_advisers(
    number_of_advisers: int,
):
    print('\nGenerating advisers...')  # noqa
    with transaction.atomic():
        teams = Team.objects.all()
        advisers_to_create = []
        for index in range(number_of_advisers):
            advisers_to_create.append(
                AdviserFactory.build(dit_team=random_object_from_queryset(teams)),
            )
            # Print progress every 10 iterations and on the last iteration
            if (index + 1) % 10 == 0 or index == number_of_advisers - 1:
                print_progress(
                    iteration=index + 1,
                    total=number_of_advisers,
                )
        AdviserFactory._meta.model.objects.bulk_create(advisers_to_create)

        print(f'\nGenerated {number_of_advisers} advisers')  # noqa
