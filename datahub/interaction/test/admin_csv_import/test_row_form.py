from collections import Counter
from collections.abc import Mapping
from datetime import date, datetime, time
from unittest.mock import Mock

import pytest
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils.timezone import utc
from rest_framework import serializers

from datahub.company.contact_matching import ContactMatchingStatus
from datahub.company.test.factories import AdviserFactory, ContactFactory
from datahub.core.exceptions import DataHubException
from datahub.event.test.factories import DisabledEventFactory, EventFactory
from datahub.interaction.admin_csv_import.duplicate_checking import DuplicateTracker
from datahub.interaction.admin_csv_import.row_form import (
    ADVISER_2_IS_THE_SAME_AS_ADVISER_1,
    ADVISER_NOT_FOUND_MESSAGE,
    ADVISER_WITH_TEAM_NOT_FOUND_MESSAGE,
    CSVRowError,
    DUPLICATE_OF_ANOTHER_ROW_MESSAGE,
    DUPLICATE_OF_EXISTING_INTERACTION_MESSAGE,
    InteractionCSVRowForm,
    MULTIPLE_ADVISERS_FOUND_MESSAGE,
    OBJECT_DISABLED_MESSAGE,
)
from datahub.interaction.models import Interaction
from datahub.interaction.test.admin_csv_import.utils import random_communication_channel
from datahub.interaction.test.factories import (
    CommunicationChannelFactory,
    CompanyInteractionFactory,
)
from datahub.interaction.test.utils import random_service
from datahub.metadata.test.factories import ChildServiceFactory, ServiceFactory, TeamFactory

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


class TestCSVRowError:
    """Tests for CSVRowError."""

    @pytest.mark.parametrize(
        'field,expected_display_field',
        (
            ('a_field', 'a_field'),
            (NON_FIELD_ERRORS, ''),
        ),
    )
    def test_display_field(self, field, expected_display_field):
        """Tests the display_field property."""
        csv_row_error = CSVRowError(1, field, '', '')
        assert csv_row_error.display_field == expected_display_field

    @pytest.mark.parametrize(
        'source_row,expected_display_source_row',
        (
            (0, 2),
            (1, 3),
        ),
    )
    def test_display_source_row(self, source_row, expected_display_source_row):
        """Test the display_source_row property."""
        csv_row_error = CSVRowError(source_row, 'some_field', '', '')
        assert csv_row_error.display_source_row == expected_display_source_row


@pytest.mark.django_db
class TestInteractionCSVRowFormValidation:
    """Tests for validation in InteractionCSVRowForm."""

    @pytest.mark.parametrize(
        'data,errors',
        (
            pytest.param(
                {'kind': ''},
                {'kind': ['This field is required.']},
                id='kind blank',
            ),
            pytest.param(
                {'kind': 'invalid'},
                {'kind': ['Select a valid choice. invalid is not one of the available choices.']},
                id='kind invalid',
            ),
            pytest.param(
                {'theme': ''},
                {'theme': ['This field is required.']},
                id='theme blank',
            ),
            pytest.param(
                {'theme': 'invalid'},
                {'theme': ['Select a valid choice. invalid is not one of the available choices.']},
                id='theme invalid',
            ),
            pytest.param(
                {
                    'kind': Interaction.KINDS.service_delivery,
                    'theme': Interaction.THEMES.investment,
                },
                {
                    'kind': ["This value can't be selected for investment interactions."],
                },
                id='investment service delivery',
            ),
            pytest.param(
                {'date': ''},
                {'date': ['This field is required.']},
                id='date blank',
            ),
            pytest.param(
                {'date': '08/31/2020'},
                {'date': ['Enter a valid date.']},
                id='invalid date',
            ),
            pytest.param(
                {'contact_email': 'invalid'},
                {'contact_email': ['Enter a valid email address.']},
                id='invalid contact_email',
            ),
            pytest.param(
                {'adviser_1': ''},
                {'adviser_1': ['This field is required.']},
                id='blank adviser_1',
            ),
            pytest.param(
                {'adviser_1': 'Non-existent adviser'},
                {'adviser_1': [ADVISER_NOT_FOUND_MESSAGE]},
                id="adviser_1 doesn't exist",
            ),
            pytest.param(
                {
                    'adviser_1': lambda: AdviserFactory.create_batch(
                        2,
                        first_name='Pluto',
                        last_name='Doris',
                    )[0].name,
                },
                {'adviser_1': [MULTIPLE_ADVISERS_FOUND_MESSAGE]},
                id='multiple matching values for adviser_1',
            ),
            pytest.param(
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
                id='adviser_1 and team_1 mismatch',
            ),
            pytest.param(
                {'adviser_2': 'Non-existent adviser'},
                {'adviser_2': [ADVISER_NOT_FOUND_MESSAGE]},
                id="adviser_2 doesn't exist",
            ),
            pytest.param(
                {
                    'adviser_2': lambda: AdviserFactory.create_batch(
                        2,
                        first_name='Pluto',
                        last_name='Doris',
                    )[0].name,
                },
                {'adviser_2': [MULTIPLE_ADVISERS_FOUND_MESSAGE]},
                id='multiple matching values for adviser_2',
            ),
            pytest.param(
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
                id='adviser_2 and team_2 mismatch',
            ),
            pytest.param(
                {
                    'adviser_1': lambda: AdviserFactory(
                        first_name='Pluto',
                        last_name='Doris',
                        dit_team__name='Team Advantage',
                    ).name,
                    'team_1': 'Team Advantage',
                    'adviser_2': 'Pluto Doris',
                    'team_2': 'Team Advantage',
                },
                {'adviser_2': [ADVISER_2_IS_THE_SAME_AS_ADVISER_1]},
                id='adviser_2 same as adviser_1',
            ),
            pytest.param(
                {'service': 'Non-existent service'},
                {
                    'service': [
                        'Select a valid choice. That choice is not one of the available choices.',
                    ],
                },
                id="service doesn't exist",
            ),
            pytest.param(
                {
                    'service': lambda: random_service(disabled=True).name,
                },
                {
                    'service': [OBJECT_DISABLED_MESSAGE],
                },
                id='service is disabled',
            ),
            pytest.param(
                {
                    'service': lambda: ServiceFactory.create_batch(2, segment='Duplicate')[0].name,
                },
                {
                    'service': ['There is more than one matching service.'],
                },
                id='multiple matching services',
            ),
            pytest.param(
                {'communication_channel': 'Non-existent communication channel'},
                {
                    'communication_channel': [
                        'Select a valid choice. That choice is not one of the available choices.',
                    ],
                },
                id="communication_channel doesn't exist",
            ),
            pytest.param(
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
                id='multiple matching communication channels',
            ),
            pytest.param(
                {
                    'communication_channel': lambda: random_communication_channel(
                        disabled=True,
                    ).name,
                },
                {
                    'communication_channel': [OBJECT_DISABLED_MESSAGE],
                },
                id='communication_channel is disabled',
            ),
            # This error comes from the serialiser validation rules
            pytest.param(
                {
                    'communication_channel': '',
                    'kind': Interaction.KINDS.interaction,
                },
                {
                    'communication_channel': ['This field is required.'],
                },
                id='communication_channel required for interactions',
            ),
            pytest.param(
                {'event_id': 'non_existent_event_id'},
                {
                    'event_id': [
                        "'non_existent_event_id' is not a valid UUID.",
                    ],
                },
                id='event_id invalid',
            ),
            pytest.param(
                {
                    'event_id': lambda: str(DisabledEventFactory().pk),
                },
                {
                    'event_id': [OBJECT_DISABLED_MESSAGE],
                },
                id='event_id is for a disabled event',
            ),
            pytest.param(
                {'event_id': '00000000-0000-0000-0000-000000000000'},
                {
                    'event_id': [
                        'Select a valid choice. That choice is not one of the available '
                        'choices.',
                    ],
                },
                id='event_id non-existent',
            ),
            # This error comes from the serialiser validation rules
            pytest.param(
                {
                    'kind': Interaction.KINDS.interaction,
                    'event_id': lambda: str(EventFactory().pk),
                },
                {
                    'event_id': ['This field is only valid for service deliveries.'],
                },
                id='cannot specify event_id for an interaction',
            ),
        ),
    )
    def test_validation_errors(self, data, errors):
        """Test validation for various fields."""
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        contact = ContactFactory(email='unique@company.com')
        service = random_service()
        communication_channel = random_communication_channel()

        resolved_data = {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.KINDS.interaction,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': contact.email,
            'service': service.name,
            'communication_channel': communication_channel.name,

            **_resolve_data(data),
        }

        form = InteractionCSVRowForm(data=resolved_data)
        assert form.errors == errors

    @pytest.mark.parametrize(
        'row_data,existing_objects_data,expected_errors',
        (
            pytest.param(
                {
                    'contact': lambda: ContactFactory(email='unique@company.com'),
                    'service': random_service,
                    'date': date(2018, 1, 1),
                },
                [],
                {},
                id='without any existing objects',
            ),
            pytest.param(
                {
                    'contact': lambda: ContactFactory(email='unique@company.com'),
                    'service': random_service,
                    'date': date(2018, 1, 1),
                },
                [
                    {
                        'contact': lambda row_data: row_data['contact'],
                        'service': lambda row_data: row_data['service'],
                        'date': lambda row_data: row_data['date'],
                    },
                ],
                {
                    NON_FIELD_ERRORS: [DUPLICATE_OF_EXISTING_INTERACTION_MESSAGE],
                },
                id='with an existing duplicate',
            ),
            pytest.param(
                {
                    'contact': lambda: ContactFactory(email='unique@company.com'),
                    'service': random_service,
                    'date': date(2018, 1, 1),
                },
                [
                    {
                        'contact': lambda _: ContactFactory(email='different@company.com'),
                        'service': lambda row_data: row_data['service'],
                        'date': lambda row_data: row_data['date'],
                    },
                ],
                {},
                id='with contact different',
            ),
            pytest.param(
                {
                    'contact': lambda: ContactFactory(email='unique@company.com'),
                    'service': random_service,
                    'date': date(2018, 1, 1),
                },
                [
                    {
                        'contact': lambda row_data: row_data['contact'],
                        'service': lambda _: ServiceFactory(),
                        'date': lambda row_data: row_data['date'],
                    },
                ],
                {},
                id='with service different',
            ),
            pytest.param(
                {
                    'contact': lambda: ContactFactory(email='unique@company.com'),
                    'service': random_service,
                    'date': date(2018, 1, 1),
                },
                [
                    {
                        'contact': lambda row_data: row_data['contact'],
                        'service': lambda row_data: row_data['service'],
                        'date': lambda row_data: date(2019, 5, 5),
                    },
                ],
                {},
                id='with date different',
            ),
        ),
    )
    def test_fails_validation_if_is_duplicate_of_existing_interaction(
        self,
        row_data,
        existing_objects_data,
        expected_errors,
    ):
        """
        Test that an error is returned if the interaction is a duplicate of an existing
        record.
        """
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        communication_channel = random_communication_channel()

        resolved_row_data = _resolve_data(row_data)
        resolved_existing_objects_data = [
            {
                key: value(resolved_row_data)
                for key, value in duplicate_item.items()
            }
            for duplicate_item in existing_objects_data
        ]

        for existing_object_data in resolved_existing_objects_data:
            CompanyInteractionFactory(
                contacts=[existing_object_data['contact']],
                company=existing_object_data['contact'].company,
                date=datetime.combine(existing_object_data['date'], time(), tzinfo=utc),
                # Unfortunately, the factory sets service_id, so we have to as well (instead
                # of service)
                service_id=existing_object_data['service'].pk,
            )

        data = {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.KINDS.interaction,
            'adviser_1': adviser.name,
            'communication_channel': communication_channel.name,

            'contact_email': resolved_row_data['contact'].email,
            'service': resolved_row_data['service'].name,
            'date': resolved_row_data['date'].strftime('%d/%m/%Y'),
        }

        form = InteractionCSVRowForm(data=data)
        assert form.errors == expected_errors

    @pytest.mark.parametrize(
        'row_data,prior_rows,expected_errors',
        (
            pytest.param(
                {
                    'contact': lambda: ContactFactory(email='unique@company.com'),
                    'service': random_service,
                    'date': date(2018, 1, 1),
                },
                [],
                {},
                id='without any existing items',
            ),
            pytest.param(
                {
                    'contact': lambda: ContactFactory(email='unique@company.com'),
                    'service': random_service,
                    'date': date(2018, 1, 1),
                },
                [
                    {
                        'contact': lambda row_data: row_data['contact'],
                        'service': lambda row_data: row_data['service'],
                        'date': lambda row_data: row_data['date'],
                    },
                ],
                {
                    NON_FIELD_ERRORS: [DUPLICATE_OF_ANOTHER_ROW_MESSAGE],
                },
                id='with an existing duplicate',
            ),
            pytest.param(
                {
                    'contact': lambda: ContactFactory(email='unique@company.com'),
                    'service': random_service,
                    'date': date(2018, 1, 1),
                },
                [
                    {
                        'contact': lambda _: ContactFactory(email='different@company.com'),
                        'service': lambda row_data: row_data['service'],
                        'date': lambda row_data: row_data['date'],
                    },
                ],
                {},
                id='with contact different',
            ),
            pytest.param(
                {
                    'contact': lambda: ContactFactory(email='unique@company.com'),
                    'service': random_service,
                    'date': date(2018, 1, 1),
                },
                [
                    {
                        'contact': lambda row_data: row_data['contact'],
                        'service': lambda _: ServiceFactory(),
                        'date': lambda row_data: row_data['date'],
                    },
                ],
                {},
                id='with service different',
            ),
            pytest.param(
                {
                    'contact': lambda: ContactFactory(email='unique@company.com'),
                    'service': random_service,
                    'date': date(2018, 1, 1),
                },
                [
                    {
                        'contact': lambda row_data: row_data['contact'],
                        'service': lambda row_data: row_data['service'],
                        'date': lambda row_data: date(2019, 5, 5),
                    },
                ],
                {},
                id='with date different',
            ),
        ),
    )
    def test_fails_validation_if_is_duplicate_of_another_row(
        self,
        row_data,
        prior_rows,
        expected_errors,
    ):
        """
        Test that an error is returned if the interaction is a duplicate of a row encountered
        earlier in the file being imported.
        """
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        communication_channel = random_communication_channel()

        resolved_row_data = _resolve_data(row_data)
        resolved_prior_rows = [
            {
                key: value(resolved_row_data)
                for key, value in duplicate_item.items()
            }
            for duplicate_item in prior_rows
        ]

        duplicate_tracker = DuplicateTracker()
        for resolved_duplicate_item in resolved_prior_rows:
            duplicate_tracker.add_item(resolved_duplicate_item)

        data = {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.KINDS.interaction,
            'adviser_1': adviser.name,
            'communication_channel': communication_channel.name,

            'contact_email': resolved_row_data['contact'].email,
            'service': resolved_row_data['service'].name,
            'date': resolved_row_data['date'].strftime('%d/%m/%Y'),
        }

        form = InteractionCSVRowForm(data=data, duplicate_tracker=duplicate_tracker)
        assert form.errors == expected_errors

    def test_does_not_look_up_blank_contact_email(self, monkeypatch):
        """Test that, if a blank contact email is provided, a contact look-up is not attempted."""
        mock_find_active_contact_by_email_address = Mock(
            return_value=(None, None),
        )
        monkeypatch.setattr(
            'datahub.interaction.admin_csv_import.row_form.find_active_contact_by_email_address',
            mock_find_active_contact_by_email_address,
        )

        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        service = random_service(disabled=False)
        communication_channel = random_communication_channel()

        data = {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.KINDS.interaction,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'service': service.name,
            'communication_channel': communication_channel.name,

            'contact_email': '',
        }
        form = InteractionCSVRowForm(data=data)
        assert form.errors == {
            'contact_email': ['This field is required.'],
        }
        assert not mock_find_active_contact_by_email_address.called


@pytest.mark.django_db
class TestInteractionCSVRowFormSerializerUsage:
    """
    Tests general logic of InteractionSerializer validators usage in InteractionCSVRowForm.

    (This excludes validation of specific fields which is part of the validation tests above.)
    """

    def test_serializer_error_for_invalid_form(self, monkeypatch):
        """
        Test that an unmapped error from the serializer validators is not added to
        NON_FIELD_ERRORS if the form was otherwise invalid.
        """
        def validator(_):
            raise serializers.ValidationError(
                {'non_existent_field': 'test error'},
            )

        monkeypatch.setattr(
            'datahub.interaction.serializers.InteractionSerializer.validators',
            [validator],
        )

        data = {'kind': 'invalid'}
        form = InteractionCSVRowForm(data=data)

        assert NON_FIELD_ERRORS not in form.errors

    def test_serializer_errors_for_valid_form(self, monkeypatch):
        """Test that errors from the serializer validators are added to the form."""
        def validator(_):
            raise serializers.ValidationError(
                {
                    # This rule should be mapped to NON_FIELD_ERRORS
                    'non_existent_field': 'unmapped test error',
                    # This rule should be mapped to adviser_2
                    'adviser_2': 'adviser test error',
                },
            )

        monkeypatch.setattr(
            'datahub.interaction.serializers.InteractionSerializer.validators',
            [validator],
        )

        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        contact = ContactFactory(email='unique@company.com')
        service = random_service()
        communication_channel = random_communication_channel()

        data = {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.KINDS.interaction,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': contact.email,
            'service': service.name,
            'communication_channel': communication_channel.name,
        }

        form = InteractionCSVRowForm(data=data)
        assert form.errors == {
            'adviser_2': ['adviser test error'],
            NON_FIELD_ERRORS: ['non_existent_field: unmapped test error'],
        }


@pytest.mark.django_db
class TestInteractionCSVRowFormSuccessfulCleaning:
    """
    Tests for successful field cleaning in InteractionCSVRowForm.

    This includes looking up model objects and the transformation of values.
    """

    @pytest.mark.parametrize(
        'field,input_value,expected_value',
        (
            pytest.param(
                'date',
                '1/2/2013',
                date(2013, 2, 1),
                id='UK date format without leading zeroes',
            ),
            pytest.param(
                'date',
                '03/04/2015',
                date(2015, 4, 3),
                id='UK date format with leading zeroes',
            ),
            pytest.param(
                'date',
                '2016-05-04',
                date(2016, 5, 4),
                id='ISO date format',
            ),
            pytest.param(
                'subject',
                'A subject',
                'A subject',
                id='subject',
            ),
            pytest.param(
                'notes',
                'Notes with\nmultiple lines\n',
                'Notes with\nmultiple lines',
                id='notes (trailing blank lines are stripped)',
            ),
        ),
    )
    def test_common_non_relations(self, field, input_value, expected_value):
        """Test the conversion and cleaning of various non-relationship fields."""
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        service = random_service()
        communication_channel = random_communication_channel()

        resolved_data = {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.KINDS.interaction,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': 'person@company.com',
            'service': service.name,
            'communication_channel': communication_channel.name,

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
            pytest.param(
                'adviser_1',
                lambda: AdviserFactory(
                    first_name='Pluto',
                    last_name='Doris',
                ),
                lambda obj: obj.name,
                id='adviser_1 look-up (same case)',
            ),
            pytest.param(
                'adviser_1',
                lambda: AdviserFactory(
                    first_name='Pluto',
                    last_name='Doris',
                ),
                lambda obj: obj.name.upper(),
                id='adviser_1 look-up (case-insensitive)',
            ),
            pytest.param(
                'adviser_2',
                lambda: AdviserFactory(
                    first_name='Pluto',
                    last_name='Doris',
                ),
                lambda obj: obj.name,
                id='adviser_2 look-up (same case)',
            ),
            pytest.param(
                'adviser_2',
                lambda: AdviserFactory(
                    first_name='Pluto',
                    last_name='Doris',
                ),
                lambda obj: obj.name.upper(),
                id='adviser_2 look-up (case-insensitive)',
            ),
            pytest.param(
                'service',
                lambda: ServiceFactory(segment='UNIQUE EXPORT DEAL'),
                lambda obj: obj.name,
                id='service look-up (same case)',
            ),
            pytest.param(
                'service',
                lambda: ChildServiceFactory(segment='UNIQUE EXPORT', parent__segment='DEAL'),
                lambda obj: obj.name,
                id='service look-up (same case)',
            ),
            pytest.param(
                'service',
                lambda: ServiceFactory(segment='UNIQUE EXPORT DEAL'),
                lambda obj: obj.name.lower(),
                id='service look-up (case-insensitive)',
            ),
        ),
    )
    def test_common_relation_fields(self, kind, field, object_creator, input_transformer):
        """
        Test the looking up of values for relationship fields common to interactions and
        service deliveries.
        """
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        service = random_service()
        communication_channel = random_communication_channel()
        obj = object_creator()

        resolved_data = {
            'theme': Interaction.THEMES.export,
            'kind': kind,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': 'person@company.com',
            'service': service.name,
            'communication_channel': communication_channel.name,

            field: input_transformer(obj),
        }

        form = InteractionCSVRowForm(data=resolved_data)
        assert not form.errors
        assert form.cleaned_data[field] == obj

    @pytest.mark.parametrize(
        'field,object_creator,input_transformer',
        (
            pytest.param(
                'communication_channel',
                lambda: random_communication_channel(),
                lambda obj: obj.name,
                id='communication channel look-up (same case)',
            ),
            pytest.param(
                'communication_channel',
                lambda: random_communication_channel(),
                lambda obj: obj.name.upper(),
                id='communication channel look-up (case-insensitive)',
            ),
        ),
    )
    def test_interaction_relation_fields(self, field, object_creator, input_transformer):
        """Test the looking up of values for relationship fields specific to interactions."""
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        contact = ContactFactory(email='unique@company.com')
        service = random_service()
        obj = object_creator()

        resolved_data = {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.KINDS.interaction,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': contact.email,
            'service': service.name,

            field: input_transformer(obj),
        }

        form = InteractionCSVRowForm(data=resolved_data)
        assert not form.errors
        assert form.cleaned_data[field] == obj

    @pytest.mark.parametrize(
        'field,object_creator,input_transformer,expected_value_transformer',
        (
            pytest.param(
                'communication_channel',
                lambda: random_communication_channel(),
                lambda obj: obj.name,
                lambda obj: None,
                id='communication channel should be ignored',
            ),
            pytest.param(
                'event_id',
                lambda: EventFactory(),
                lambda obj: str(obj.pk),
                lambda obj: obj,
                id='event look-up',
            ),
            pytest.param(
                'event_id',
                lambda: None,
                lambda _: '',
                lambda _: None,
                id='event can be omitted',
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
        contact = ContactFactory(email='unique@company.com')
        service = random_service()
        obj = object_creator()

        resolved_data = {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.KINDS.service_delivery,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': contact.email,
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
        service = random_service()
        communication_channel = random_communication_channel()

        data = {
            'theme': Interaction.THEMES.export,
            'kind': kind,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': 'person@company.com',
            'service': service.name,
            'communication_channel': communication_channel.name,
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
        service = random_service(disabled=False)

        communication_channel = random_communication_channel()

        data = {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.KINDS.interaction,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'service': service.name,
            'communication_channel': communication_channel.name,

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


@pytest.mark.django_db
class TestInteractionCSVRowFormGetFlatErrorListIterator:
    """Tests for InteractionCSVRowForm.get_flat_error_list_iterator()."""

    def test_get_flat_error_list_iterator(self):
        """Test that get_flat_error_list_iterator() returns a flat list of errors."""
        data = {
            'theme': 'invalid',
            'kind': 'invalid',
            'date': 'invalid',
            'adviser_1': '',
            'contact_email': '',
            'service': '',
        }

        form = InteractionCSVRowForm(data=data, row_index=5)
        form.is_valid()

        expected_errors = [
            CSVRowError(
                5,
                'kind',
                'invalid',
                'Select a valid choice. invalid is not one of the available choices.',
            ),
            CSVRowError(
                5,
                'theme',
                'invalid',
                'Select a valid choice. invalid is not one of the available choices.',
            ),
            CSVRowError(
                5,
                'date',
                'invalid',
                'Enter a valid date.',
            ),
            CSVRowError(
                5,
                'adviser_1',
                '',
                'This field is required.',
            ),
            CSVRowError(
                5,
                'contact_email',
                '',
                'This field is required.',
            ),
            CSVRowError(
                5,
                'service',
                '',
                'This field is required.',
            ),
        ]
        assert Counter(form.get_flat_error_list_iterator()) == Counter(expected_errors)


@pytest.mark.django_db
class TestInteractionCSVRowFormCleanedDataAsSerializerDict:
    """Tests for InteractionCSVRowForm.cleaned_data_as_serializer_dict()."""

    def test_cleaned_data_as_serializer_dict_for_interaction(self):
        """Test that cleaned_data_as_serializer_dict() transforms an interaction."""
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        contact = ContactFactory(email='unique@company.com')
        service = random_service()
        communication_channel = random_communication_channel()

        data = {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.KINDS.interaction,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': contact.email,
            'service': service.name,
            'communication_channel': communication_channel.name,
        }
        form = InteractionCSVRowForm(data=data)

        assert form.is_valid()
        assert form.cleaned_data_as_serializer_dict() == {
            'contacts': [contact],
            'communication_channel': communication_channel,
            'company': contact.company,
            'date': datetime(2018, 1, 1, tzinfo=utc),
            'dit_participants': [
                {
                    'adviser': adviser,
                    'team': adviser.dit_team,
                },
            ],
            'event': None,
            'kind': data['kind'],
            'notes': '',
            'service': service,
            'status': Interaction.STATUSES.complete,
            'subject': service.name,
            'theme': data['theme'],
            'was_policy_feedback_provided': False,
        }

    def test_cleaned_data_as_serializer_dict_for_service_delivery(self):
        """Test that cleaned_data_as_serializer_dict() transforms a service delivery."""
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        contact = ContactFactory(email='unique@company.com')
        service = random_service()
        event = EventFactory()

        data = {
            'theme': Interaction.THEMES.other,
            'kind': Interaction.KINDS.service_delivery,
            'date': '01/01/2018',
            'adviser_1': adviser.name,
            'contact_email': contact.email,
            'service': service.name,
            'event_id': str(event.pk),
            'subject': 'Test subject',
            'notes': 'Some notes',
        }
        form = InteractionCSVRowForm(data=data)

        assert form.is_valid()
        assert form.cleaned_data_as_serializer_dict() == {
            'contacts': [contact],
            'communication_channel': None,
            'company': contact.company,
            'date': datetime(2018, 1, 1, tzinfo=utc),
            'dit_participants': [
                {
                    'adviser': adviser,
                    'team': adviser.dit_team,
                },
            ],
            'event': event,
            'is_event': True,
            'kind': data['kind'],
            'notes': data['notes'],
            'service': service,
            'status': Interaction.STATUSES.complete,
            'subject': data['subject'],
            'theme': data['theme'],
            'was_policy_feedback_provided': False,
        }


@pytest.mark.django_db
class TestInteractionCSVRowFormSaving:
    """Tests for InteractionCSVRowForm.save()."""

    def test_save_interaction(self):
        """Test saving an interaction."""
        user = AdviserFactory(first_name='Admin', last_name='User')
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        contact = ContactFactory(email='unique@company.com')
        service = random_service()
        communication_channel = random_communication_channel()
        source = {'test-source': 'test-value'}

        data = {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.KINDS.interaction,
            'date': '02/03/2018',
            'adviser_1': adviser.name,
            'contact_email': contact.email,
            'service': service.name,
            'communication_channel': communication_channel.name,
        }
        form = InteractionCSVRowForm(data=data)

        assert form.is_valid()
        interaction = form.save(user, source=source)
        interaction.refresh_from_db()

        assert interaction.theme == data['theme']
        assert interaction.kind == data['kind']
        assert interaction.date == datetime(2018, 3, 2, tzinfo=utc)
        assert interaction.communication_channel == communication_channel
        assert interaction.service == service
        assert interaction.status == Interaction.STATUSES.complete
        assert interaction.subject == service.name
        assert interaction.event is None
        assert interaction.notes == ''
        assert interaction.created_by == user
        assert interaction.modified_by == user
        assert interaction.source == source

        assert list(interaction.contacts.all()) == [contact]
        assert interaction.dit_participants.count() == 1

        dit_participant = interaction.dit_participants.first()
        assert dit_participant.adviser == adviser
        assert dit_participant.team == adviser.dit_team

    def test_save_service_delivery(self):
        """Test saving a service delivery."""
        user = AdviserFactory(first_name='Admin', last_name='User')
        adviser_1 = AdviserFactory(first_name='Neptune', last_name='Doris')
        adviser_2 = AdviserFactory(first_name='Pluto', last_name='Greene')
        contact = ContactFactory(email='unique@company.com')
        service = random_service()
        event = EventFactory()
        source = {'test-source': 'test-value'}

        data = {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.KINDS.service_delivery,
            'date': '02/03/2018',
            'adviser_1': adviser_1.name,
            'adviser_2': adviser_2.name,
            'contact_email': contact.email,
            'service': service.name,
            'event_id': str(event.pk),
            'subject': 'Test subject',
            'notes': 'Some notes',
        }
        form = InteractionCSVRowForm(data=data)

        assert form.is_valid()
        interaction = form.save(user, source=source)
        interaction.refresh_from_db()

        assert interaction.theme == data['theme']
        assert interaction.kind == data['kind']
        assert interaction.date == datetime(2018, 3, 2, tzinfo=utc)
        assert interaction.event == event
        assert interaction.service == service
        assert interaction.status == Interaction.STATUSES.complete
        assert interaction.subject == data['subject']
        assert interaction.event == event
        assert interaction.notes == data['notes']
        assert interaction.created_by == user
        assert interaction.modified_by == user
        assert interaction.source == source

        assert list(interaction.contacts.all()) == [contact]
        assert interaction.dit_participants.count() == 2

        actual_advisers_and_teams = Counter(
            (dit_participant.adviser, dit_participant.team)
            for dit_participant in interaction.dit_participants.all()
        )
        expected_advisers_and_teams = Counter(
            (
                (adviser_1, adviser_1.dit_team),
                (adviser_2, adviser_2.dit_team),
            ),
        )

        assert actual_advisers_and_teams == expected_advisers_and_teams

    def test_save_with_unmatched_contact_raises_error(self):
        """Test that saving an interaction with an unmatched contact raises an error."""
        user = AdviserFactory(first_name='Admin', last_name='User')
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        service = random_service()
        communication_channel = random_communication_channel()
        source = {'test-source': 'test-value'}

        data = {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.KINDS.interaction,
            'date': '02/03/2018',
            'adviser_1': adviser.name,
            'contact_email': 'non-existent-contact@company.com',
            'service': service.name,
            'communication_channel': communication_channel.name,
        }
        form = InteractionCSVRowForm(data=data)

        assert form.is_valid()
        assert not form.is_matched()

        with pytest.raises(DataHubException):
            form.save(user, source=source)

    def test_save_rolls_back_on_error(self, monkeypatch):
        """Test that save() rolls back if there's an error."""
        monkeypatch.setattr(
            'datahub.interaction.admin_csv_import.row_form.InteractionDITParticipant',
            Mock(side_effect=ValueError),
        )

        user = AdviserFactory(first_name='Admin', last_name='User')
        adviser = AdviserFactory(first_name='Neptune', last_name='Doris')
        contact = ContactFactory(email='unique@company.com')
        service = random_service()
        communication_channel = random_communication_channel()
        source = {'test-source': 'test-value'}

        data = {
            'theme': Interaction.THEMES.export,
            'kind': Interaction.KINDS.interaction,
            'date': '02/03/2018',
            'adviser_1': adviser.name,
            'contact_email': contact.email,
            'service': service.name,
            'communication_channel': communication_channel.name,
        }
        form = InteractionCSVRowForm(data=data)

        assert form.is_valid()

        with pytest.raises(ValueError):
            form.save(user, source=source)

        assert not Interaction.objects.exists()


def _resolve_data(data):
    """Resolve callables in values used in parametrised tests."""
    if isinstance(data, Mapping):
        return {key: _resolve_data(value) for key, value in data.items()}

    if callable(data):
        return data()

    return data
