from itertools import chain, product, repeat
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.db import transaction

from datahub.cleanup.management.commands.delete_orphaned_teams import Command
from datahub.company.models import Company
from datahub.company.models.adviser import Advisor
from datahub.company.models.contact import Contact
from datahub.event.models import Event, EventType
from datahub.metadata.models import Country, Team
from datahub.omis.order.models import Order, OrderAssignee


def power_set(s):
    """Returns a *power set* for the set ``s``"""
    return set(map(frozenset, product(*repeat(s, len(s))))) | {frozenset()}


@pytest.fixture
@pytest.mark.django_db
def with_empty_teams():
    """
    A fixture which ensures that the test runs with an empty
    :class:`datahub.metadata.models.Team` model.

    The state of the model will be restored after each test.
    """
    with transaction.atomic():
        original_items = set(Team.objects.all())
        savepoint = transaction.savepoint()
        Team.objects.all().delete()
        assert Team.objects.count() == 0

        yield

        transaction.savepoint_rollback(savepoint)
        assert set(Team.objects.all()) == original_items


# We are not using the existing model factories, because they pollute the
# metadata.Team model with lot of records, complicating assertions about them.
def order_assignee_factory(team):
    """
    Creates a :class:`datahub.omis.order.models.OrderAssignee` instance related to ``team``
    """
    adviser = Advisor.objects.create(
        first_name='John',
        last_name='Doe',
        email=f'{uuid4()}@example.com',
    )
    order_assignee = OrderAssignee.objects.create(
        order=Order.objects.create(
            company=Company.objects.create(),
            contact=Contact.objects.create(primary=True),
            primary_market=Country.objects.create(),
        ),
        adviser=adviser,
        created_by=adviser)
    order_assignee.team = team
    order_assignee.save()
    return order_assignee


def event_with_lead_team_factory(team):
    """
    Creates a :class:`datahub.event.models.Event` instance with ``team`` assigned
    to ``Event.lead_team``.
    """
    return Event.objects.create(
        event_type=EventType.objects.create(),
        address_country=Country.objects.create(),
        lead_team=team,
    )


def event_with_teams_factory(team):
    """
    Creates a :class:`datahub.event.models.Event` instance with ``team`` assigned
    to ``Event.teams``.
    """
    event = Event.objects.create(
        event_type=EventType.objects.create(),
        address_country=Country.objects.create(),
    )
    event.teams.add(team)
    return event


def adviser_factory(team):
    """
    Creates a :class:`datahub.company.models.adviser.Advisor` related to ``team``.
    """
    return Advisor.objects.create(email=f'{uuid4()}@example.com', dit_team=team)


# Team can be related to Event in two ways, the Event.lead_team relation is
# represented by the Event model and the Event.teams by this constant.
EVENT_TEAMS = 'EVENT_TEAMS'


# Maps Team relationships (as models) to related model instance factories
RELATIONSHIP_FACTORY_MAP = {
    Advisor: adviser_factory,
    OrderAssignee: order_assignee_factory,
    Event: event_with_lead_team_factory,
    EVENT_TEAMS: event_with_teams_factory,
}


RELATIONS_POWER_SET = power_set({OrderAssignee, Event, Advisor, EVENT_TEAMS})


@pytest.mark.parametrize('teams', [
    # All possible relation combinations
    RELATIONS_POWER_SET,
    # Only non-related teams
    repeat((), 7),
    # Plenty of related and non-related teams
    chain(repeat((), 5), chain(*repeat(RELATIONS_POWER_SET, 3))),
])
@pytest.mark.django_db
def test_command(teams, with_empty_teams):
    """
    Tests the :class:`datahub.cleanup.management.commands.delete_orphaned_teams.Command`
    """
    should_be_deleted = set()
    should_stay = set()
    for related_models in teams:
        team = Team.objects.create(tags=[])
        relations = [RELATIONSHIP_FACTORY_MAP[model](team) for model in related_models]
        (should_stay if relations else should_be_deleted).add(team)

    assert should_be_deleted & should_stay == set(),\
        'The sets of related and non-related teams should have no overlap'
    assert set(Team.objects.all()) == should_stay | should_be_deleted,\
        'The model should have both related and non-related teams'

    call_command(Command())

    assert set(Team.objects.all()) == should_stay, \
        'The model should only have related teams'
