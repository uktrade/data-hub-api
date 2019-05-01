from collections.abc import Mapping
from datetime import date

import pytest

from datahub.company.contact_matching import ContactMatchingStatus
from datahub.company.test.factories import AdviserFactory, ContactFactory
from datahub.core.test_utils import random_obj_for_queryset
from datahub.event.test.factories import DisabledEventFactory, EventFactory
from datahub.interaction.admin_csv_import.row_form import (
    ADVISER_NOT_FOUND_MESSAGE,
    ADVISER_WITH_TEAM_NOT_FOUND_MESSAGE,
    INTERACTION_CANNOT_HAVE_AN_EVENT_MESSAGE,
    InteractionCSVRowForm,
    MULTIPLE_ADVISERS_FOUND_MESSAGE,
    OBJECT_DISABLED_MESSAGE,
)
from datahub.interaction.models import CommunicationChannel, Interaction
from datahub.interaction.test.factories import CommunicationChannelFactory
from datahub.metadata.models import Service
from datahub.metadata.test.factories import ServiceFactory, TeamFactory


EMAIL_MATCHING_CONTACT_TEST_DATA = [
    {
        'email': 'unique1@primary.com',
        'email_alternative': '',
    },
    {
        'email': 'unique2@primary.com',
        'email_alternative': 'unique2@alternative.com',
    },
    {
        'email': 'duplicate@primary.com',
        'email_alternative': '',
    },
    {
        'email': 'duplicate@primary.com',
        'email_alternative': '',
    },
]


@pytest.mark.django_db
class TestInteractionCSVRowForm:
    """Tests for InteractionCSVRowForm."""

    @pytest.mark.parametrize(
        'data,errors',
        (
            # kind blank
            (
                {'kind': ''},
                {'kind': ['This field is required.']},
            ),
            # kind invalid
            (
                {'kind': 'invalid'},
                {'kind': ['Select a valid choice. invalid is not one of the available choices.']},
            ),
            # date blank
            (
                {'date': ''},
                {'date': ['This field is required.']},
            ),
            # invalid date
            (
                {'date': '08/31/2020'},
                {'date': ['Enter a valid date.']},
            ),
            # invalid contact_email
            (
                {'contact_email': 'invalid'},
                {'contact_email': ['Enter a valid email address.']},
            ),
            # blank adviser_1
            (
                {'adviser_1': ''},
                {'adviser_1': ['This field is required.']},
            ),
            # adviser_1 doesn't exist
            (
                {'adviser_1': 'Non-existent adviser'},
                {'adviser_1': [ADVISER_NOT_FOUND_MESSAGE]},
            ),
            # multiple matching values for adviser_1
            (
                {
                    'adviser_1': lambda: AdviserFactory.create_batch(
                        2,
                        first_name='Pluto',
                        last_name='Doris',
                    )[0].name,
                },
                {'adviser_1': [MULTIPLE_ADVISERS_FOUND_MESSAGE]},
            ),
            # adviser_1 and team_1 mismatch
            (
                {
                    'adviser_1': lambda: AdviserFactory(
                        first_name='Pluto',
                        last_name='Doris',
                        dit_team__name='Team Advantage',
                    ).name,
                    'team_1': lambda: TeamFactory(
                        name='Team Disadvantage',
                    ).name,
                },
                {'adviser_1': [ADVISER_WITH_TEAM_NOT_FOUND_MESSAGE]},
            ),
            # adviser_2 doesn't exist
            (
                {'adviser_2': 'Non-existent adviser'},
                {'adviser_2': [ADVISER_NOT_FOUND_MESSAGE]},
            ),
            # multiple matching values for adviser_2
            (
                {
                    'adviser_2': lambda: AdviserFactory.create_batch(
                        2,
                        first_name='Pluto',
                        last_name='Doris',
                    )[0].name,
                },
                {'adviser_2': [MULTIPLE_ADVISERS_FOUND_MESSAGE]},
            ),
            # adviser_2 and team_2 mismatch
            (
                {
                    'adviser_2': lambda: AdviserFactory(
                        first_name='Pluto',
                        last_name='Doris',
                        dit_team__name='Team Advantage',
                    ).name,
                    'team_2': lambda: TeamFactory(
                        name='Team Disadvantage',
                    ).name,
                },
                {'adviser_2': [ADVISER_WITH_TEAM_NOT_FOUND_MESSAGE]},
            ),
            # service doesn't exist
            (
                {'service': 'Non-existent service'},
                {
                    'service': [
                        'Select a valid choice. That choice is not one of the available choices.',
                    ],
                },
            ),
            # service is disabled
            (
                {
                    'service': lambda: _random_service(disabled=True).name,
                },
                {
                    'service': [OBJECT_DISABLED_MESSAGE],
                },
            ),
            # Multiple matching services
            (
                {
                    'service': lambda: ServiceFactory.create_batch(2, name='Duplicate')[0].name,
                },
                {
                    'service': ['There is more than one matching service.'],
                },
            ),
            # communication_channel doesn't exist
            (
                {'communication_channel': 'Non-existent communication channel'},
                {
                    'communication_channel': [
                        'Select a valid choice. That choice is not one of the available choices.',
                    ],
                },
            ),
            # Multiple matching communication channels
            (
                {
                    'communication_channel': lambda: CommunicationChannelFactory.create_batch(
                        2,
                        name='Duplicate',
                    )[0].name,
                },
                {
                    'communication_channel': [
                        'There is more than one matching communication channel.',
                    ],
                },
            ),
            # communication_channel is disabled
            (
                {
                    'communication_channel': lambda: _random_communication_channel(
                        disabled=True,
                    ).name,
                },
                {
                    'communication_channel': [OBJECT_DISABLED_MESSAGE],
                },
            ),
            # event_id invalid
            (
                {'event_id': 'non_existent_event_id'},
                {
                    'event_id': [
                        "'non_existent_event_id' is not a valid UUID.",
                    ],
                },
            ),
            # event_id is for a disabled event
            (
                {
                    'event_id': lambda: str(DisabledEventFactory().pk),
                },
                {
                    'event_id': [OBJECT_DISABLED_MESSAGE],
                },
            ),
            # event_id non-existent
            (
                {'event_id': '00000000-0000-0000-0000-000000000000'},
                {
                    'event_id': [
                        'Select a valid choice. That choice is not one of the available '
                        'choices.',
                    ],
                },
            ),
            # cannot specify event_id for an interaction
            (
                {
                    'kind': Interaction.KINDS.interaction,
                    'event_id': lambda: str(EventFactory().pk),
                },
                {
                    'event_id': [INTERACTION_CANNOT_HAVE_AN_EVENT_MESSAGE],
                },
            ),
        ),
    )
    def test_validation_errors(self, data, errors):
        """Test validation for various fields."""
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        service = _random_service()

        resolved_data = {
            'kind': 'interaction',
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': 'person@company.com',
            'service': service.name,

            **_resolve_data(data),
        }

        form = InteractionCSVRowForm(data=resolved_data)
        assert form.errors == errors

    @pytest.mark.parametrize(
        'field,input_value,expected_value',
        (
            # UK date format without leading zeroes
            (
                'date',
                '1/2/2013',
                date(2013, 2, 1),
            ),
            # UK date format with leading zeroes
            (
                'date',
                '03/04/2015',
                date(2015, 4, 3),
            ),
            # ISO date format
            (
                'date',
                '2016-05-04',
                date(2016, 5, 4),
            ),
            # Subject
            (
                'subject',
                'A subject',
                'A subject',
            ),
            # Notes (trailing blank lines are stripped)
            (
                'notes',
                'Notes with\nmultiple lines\n',
                'Notes with\nmultiple lines',
            ),
        ),
    )
    def test_simple_value_cleaning(self, field, input_value, expected_value):
        """Test the conversion and cleaning of various non-relationship fields."""
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        service = _random_service()

        resolved_data = {
            'kind': 'interaction',
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': 'person@company.com',
            'service': service.name,

            field: input_value,
        }

        form = InteractionCSVRowForm(data=resolved_data)
        assert not form.errors
        assert form.cleaned_data[field] == expected_value

    @pytest.mark.parametrize(
        'kind',
        (Interaction.KINDS.interaction, Interaction.KINDS.service_delivery),
    )
    @pytest.mark.parametrize(
        'field,object_creator,input_transformer',
        (
            # adviser_1 look-up (same case)
            (
                'adviser_1',
                lambda: AdviserFactory(
                    first_name='Pluto',
                    last_name='Doris',
                ),
                lambda obj: obj.name,
            ),
            # adviser_1 look-up (case-insensitive)
            (
                'adviser_1',
                lambda: AdviserFactory(
                    first_name='Pluto',
                    last_name='Doris',
                ),
                lambda obj: obj.name.upper(),
            ),
            # adviser_2 look-up (same case)
            (
                'adviser_1',
                lambda: AdviserFactory(
                    first_name='Pluto',
                    last_name='Doris',
                ),
                lambda obj: obj.name,
            ),
            # adviser_2 look-up (case-insensitive)
            (
                'adviser_1',
                lambda: AdviserFactory(
                    first_name='Pluto',
                    last_name='Doris',
                ),
                lambda obj: obj.name.upper(),
            ),
            # service look-up (same case)
            (
                'service',
                lambda: ServiceFactory(name='UNIQUE EXPORT DEAL'),
                lambda obj: obj.name,
            ),
            # service look-up (case-insensitive)
            (
                'service',
                lambda: ServiceFactory(name='UNIQUE EXPORT DEAL'),
                lambda obj: obj.name.lower(),
            ),
        ),
    )
    def test_common_relation_fields(self, kind, field, object_creator, input_transformer):
        """
        Test the looking up of values for relationship fields common to interactions and
        service deliveries.
        """
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        service = _random_service()
        obj = object_creator()

        resolved_data = {
            'kind': kind,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': 'person@company.com',
            'service': service.name,

            field: input_transformer(obj),
        }

        form = InteractionCSVRowForm(data=resolved_data)
        assert not form.errors
        assert form.cleaned_data[field] == obj

    @pytest.mark.parametrize(
        'field,object_creator,input_transformer',
        (
            # communication channel look-up (same case)
            (
                'communication_channel',
                lambda: _random_communication_channel(),
                lambda obj: obj.name,
            ),
            # communication channel look-up (case-insensitive)
            (
                'communication_channel',
                lambda: _random_communication_channel(),
                lambda obj: obj.name.upper(),
            ),
        ),
    )
    def test_interaction_relation_fields(self, field, object_creator, input_transformer):
        """Test the looking up of values for relationship fields specific to interactions."""
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        service = _random_service()
        obj = object_creator()

        resolved_data = {
            'kind': 'interaction',
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': 'person@company.com',
            'service': service.name,

            field: input_transformer(obj),
        }

        form = InteractionCSVRowForm(data=resolved_data)
        assert not form.errors
        assert form.cleaned_data[field] == obj

    @pytest.mark.parametrize(
        'field,object_creator,input_transformer,expected_value_transformer',
        (
            # communication channel should be ignored
            (
                'communication_channel',
                lambda: _random_communication_channel(),
                lambda obj: obj.name,
                lambda obj: None,
            ),
            # event look-up
            (
                'event_id',
                lambda: EventFactory(),
                lambda obj: str(obj.pk),
                lambda obj: obj,
            ),
        ),
    )
    def test_service_delivery_relation_fields(
        self,
        field,
        object_creator,
        input_transformer,
        expected_value_transformer,
    ):
        """Test the looking up of values for relationship fields specific to service deliveries."""
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        service = _random_service()
        obj = object_creator()

        resolved_data = {
            'kind': 'service_delivery',
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': 'person@company.com',
            'service': service.name,

            field: input_transformer(obj),
        }

        form = InteractionCSVRowForm(data=resolved_data)
        assert not form.errors
        assert form.cleaned_data[field] == expected_value_transformer(obj)

    @pytest.mark.parametrize(
        'kind',
        (Interaction.KINDS.interaction, Interaction.KINDS.service_delivery),
    )
    def test_subject_falls_back_to_service(self, kind):
        """Test that if subject is not specified, the name of the service is used instead."""
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        service = _random_service()

        data = {
            'kind': kind,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': 'person@company.com',
            'service': service.name,
        }

        form = InteractionCSVRowForm(data=data)
        assert not form.errors
        assert form.cleaned_data['subject'] == service.name

    @pytest.mark.parametrize(
        'input_email,matching_status,match_on_alternative',
        (
            # unique match of a contact on primary email
            ('unique1@primary.com', ContactMatchingStatus.matched, False),
            # unique match of a contact on alternative email
            ('unique2@alternative.com', ContactMatchingStatus.matched, True),
            # no match of a contact
            ('UNIQUE@COMPANY.IO', ContactMatchingStatus.unmatched, False),
            # multiple matches of a contact
            ('duplicate@primary.com', ContactMatchingStatus.multiple_matches, None),
        ),
    )
    def test_contact_lookup(self, input_email, matching_status, match_on_alternative):
        """
        Test that various contact matching scenarios.

        Note that the matching logic is tested more extensively in the company app.
        """
        for factory_kwargs in EMAIL_MATCHING_CONTACT_TEST_DATA:
            ContactFactory(**factory_kwargs)

        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        service = random_obj_for_queryset(
            Service.objects.filter(disabled_on__isnull=True),
        )

        data = {
            'kind': 'interaction',
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'service': service.name,

            'contact_email': input_email,
        }
        form = InteractionCSVRowForm(data=data)
        assert not form.errors

        assert form.cleaned_data['contact_matching_status'] == matching_status

        assert 'contact' in form.cleaned_data
        contact = form.cleaned_data['contact']

        if matching_status == ContactMatchingStatus.matched:
            assert contact
            actual_email = contact.email_alternative if match_on_alternative else contact.email
            assert actual_email.lower() == input_email.lower()
        else:
            assert not contact


def _random_communication_channel(disabled=False):
    return random_obj_for_queryset(
        CommunicationChannel.objects.filter(disabled_on__isnull=not disabled),
    )


def _random_service(disabled=False):
    return random_obj_for_queryset(
        Service.objects.filter(disabled_on__isnull=not disabled),
    )


def _resolve_data(data):
    """Resolve callables in values used in parametrised tests."""
    if isinstance(data, Mapping):
        return {key: _resolve_data(value) for key, value in data.items()}

    if callable(data):
        return data()

    return data
