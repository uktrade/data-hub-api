from datahub.company.test.factories import AdviserFactory
from datahub.metadata.models import Team


from ..utils import (
    random_object_from_queryset,
    send_heartbeat_every_10_iterations,
)


def generate_advisers(
    number_of_advisers: int,
):
    teams = Team.objects.all()
    for index in range(number_of_advisers):
        AdviserFactory(
            dit_team=random_object_from_queryset(teams),
        )
        send_heartbeat_every_10_iterations(index)
    print(f'\nGenerated {number_of_advisers} advisers')  # noqa
