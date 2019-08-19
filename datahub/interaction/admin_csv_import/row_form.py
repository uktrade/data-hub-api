from datetime import datetime, time
from typing import NamedTuple

from django import forms
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db.models import Value
from django.db.transaction import atomic
from django.utils.timezone import utc
from django.utils.translation import gettext_lazy
from rest_framework import serializers

from datahub.company.contact_matching import (
    ContactMatchingStatus,
    find_active_contact_by_email_address,
)
from datahub.company.models import Advisor
from datahub.core.exceptions import DataHubException
from datahub.core.query_utils import PreferNullConcat
from datahub.core.utils import join_truthy_strings
from datahub.event.models import Event
from datahub.interaction.admin_csv_import.duplicate_checking import (
    is_duplicate_of_existing_interaction,
)
from datahub.interaction.models import (
    CommunicationChannel,
    Interaction,
    InteractionDITParticipant,
    ServiceAnswerOption,
)
from datahub.interaction.serializers import InteractionSerializer
from datahub.metadata.models import Service, Team
from datahub.metadata.query_utils import get_service_name_subquery


OBJECT_DISABLED_MESSAGE = gettext_lazy('This option is disabled.')
ADVISER_NOT_FOUND_MESSAGE = gettext_lazy(
    'An active adviser could not be found with the specified name.',
)
ADVISER_WITH_TEAM_NOT_FOUND_MESSAGE = gettext_lazy(
    'An active adviser could not be found with the specified name and team.',
)
MULTIPLE_ADVISERS_FOUND_MESSAGE = gettext_lazy(
    'Multiple matching advisers were found.',
)
ADVISER_2_IS_THE_SAME_AS_ADVISER_1 = gettext_lazy(
    'Adviser 2 cannot be the same person as adviser 1.',
)
DUPLICATE_OF_EXISTING_INTERACTION_MESSAGE = gettext_lazy(
    'This interaction appears to be a duplicate as there is an existing interaction with the '
    'same service, date and contact.',
)
DUPLICATE_OF_ANOTHER_ROW_MESSAGE = gettext_lazy(
    'This interaction appears to be a duplicate as there is another row in this file with the '
    'same service, date and contact.',
)
SERVICE_ANSWER_NOT_FOUND = gettext_lazy(
    'A service answer could not be found with the specified name and service.',
)
SERVICE_ANSWER_NOT_REQUIRED = gettext_lazy(
    'A service answer was provided when the selected service does not require it.',
)
SERVICE_ANSWER_REQUIRED = gettext_lazy(
    'A service answer is required for the specified service.',
)


def _validate_not_disabled(obj):
    if obj.disabled_on:
        raise ValidationError(OBJECT_DISABLED_MESSAGE, code='object_is_disabled')


class CSVRowError(NamedTuple):
    """A flattened validation error."""

    source_row: int
    field: str
    value: str
    error: str

    @property
    def display_field(self):
        """Returns the field name suitable for displaying to the user."""
        return '' if self.field == NON_FIELD_ERRORS else self.field

    @property
    def display_source_row(self):
        """
        Returns the source row number for displaying to the user.

        This adds 2 to source_row:

        - 1 is added for the header (column titles)
        - 1 is added to make it one-based (rather than zero-based)

        These make the displayed row numbers align with the row numbers as displayed
        in a spreadsheet editor.
        """
        return self.source_row + 2


class NoDuplicatesModelChoiceField(forms.ModelChoiceField):
    """ModelChoiceField subclass that handles MultipleObjectsReturned exceptions."""

    default_error_messages = {
        'multiple_matches': gettext_lazy('There is more than one matching %(verbose_name)s.'),
    }

    def to_python(self, value):
        """Looks up value using the query set, handling MultipleObjectsReturned exceptions."""
        model = self.queryset.model
        try:
            return super().to_python(value)
        except model.MultipleObjectsReturned:
            raise ValidationError(
                self.error_messages['multiple_matches'],
                code='multiple_matches',
                params={
                    'verbose_name': model._meta.verbose_name,
                },
            )


class InteractionCSVRowForm(forms.Form):
    """Form used for validating a single row in a CSV of interactions."""

    # Used to map errors from serializer fields to fields in this form
    # when running the serializer validators in full_clean()
    SERIALIZER_FIELD_MAPPING = {
        'event': 'event_id',
    }

    theme = forms.ChoiceField(choices=Interaction.THEMES)
    kind = forms.ChoiceField(choices=Interaction.KINDS)
    date = forms.DateField(input_formats=['%d/%m/%Y', '%Y-%m-%d'])
    # Used to attempt to find a matching contact (and company) for the interaction
    # Note that if a matching contact is not found, the interaction in question is
    # skipped (and the user informed) rather than the whole process aborting
    contact_email = forms.EmailField()
    # Represents an InteractionDITParticipant for the interaction.
    # The adviser will be looked up by name (case-insensitive) with inactive advisers
    # excluded.
    # If team_1 is provided, this will also be used to narrow down the match (useful
    # when, for example, two advisers have the same name).
    adviser_1 = forms.CharField()
    team_1 = NoDuplicatesModelChoiceField(
        Team.objects.all(),
        to_field_name='name__iexact',
        required=False,
    )
    # Represents an additional InteractionDITParticipant for the interaction
    # adviser_2 is looked up in the same way as adviser_1 (described above)
    adviser_2 = forms.CharField(required=False)
    team_2 = NoDuplicatesModelChoiceField(
        Team.objects.all(),
        to_field_name='name__iexact',
        required=False,
    )
    service = NoDuplicatesModelChoiceField(
        Service.objects.annotate(name=get_service_name_subquery()).filter(children__isnull=True),
        to_field_name='name__iexact',
        validators=[_validate_not_disabled],
    )
    service_answer = forms.CharField(required=False)

    communication_channel = NoDuplicatesModelChoiceField(
        CommunicationChannel.objects.all(),
        to_field_name='name__iexact',
        required=False,
        validators=[_validate_not_disabled],
    )
    event_id = forms.ModelChoiceField(
        Event.objects.all(),
        required=False,
        validators=[_validate_not_disabled],
    )
    # Subject is optional as it defaults to the name of the service
    subject = forms.CharField(required=False)
    notes = forms.CharField(required=False)

    def __init__(self, *args, duplicate_tracker=None, row_index=None, **kwargs):
        """Initialise the form with an optional zero-based row index."""
        super().__init__(*args, **kwargs)
        self.row_index = row_index
        self.duplicate_tracker = duplicate_tracker

    @classmethod
    def get_required_field_names(cls):
        """Get the required base fields of this form."""
        return {name for name, field in cls.base_fields.items() if field.required}

    def get_flat_error_list_iterator(self):
        """Get a generator of CSVRowError instances representing validation errors."""
        return (
            CSVRowError(self.row_index, field, self.data.get(field, ''), error)
            for field, errors in self.errors.items()
            for error in errors
        )

    def is_valid_and_matched(self):
        """Return if the form is valid and the interaction has been matched to a contact."""
        return self.is_valid() and self.is_matched()

    def is_matched(self):
        """
        Returns whether the interaction was matched to a contact.

        Can only be called post-cleaning.
        """
        return self.cleaned_data['contact_matching_status'] == ContactMatchingStatus.matched

    def clean(self):
        """Validate and clean the data for this row."""
        data = super().clean()

        kind = data.get('kind')
        subject = data.get('subject')
        service = data.get('service')
        self._populate_service_answers(data)

        # Ignore communication channel for service deliveries (as it is not a valid field for
        # service deliveries, but we are likely to get it in provided data anyway)
        if kind == Interaction.KINDS.service_delivery:
            data['communication_channel'] = None

        # Look up values for adviser_1 and adviser_2 (adding errors if the look-up fails)
        self._populate_adviser(data, 'adviser_1', 'team_1')
        self._populate_adviser(data, 'adviser_2', 'team_2')
        self._check_adviser_1_and_2_are_different(data)

        # If no subject was provided, set it to the name of the service
        if not subject and service:
            data['subject'] = service.name

        self._populate_contact(data)

        self._validate_not_duplicate_of_prior_row(data)
        self._validate_not_duplicate_of_existing_interaction(data)

        return data

    def full_clean(self):
        """
        Performs full validation, additionally performing validation using the validators
        from InteractionSerializer if the interaction was matched to a contact.

        Errors are mapped to CSV fields where possible. If not possible, they are
        added to NON_FIELD_ERRORS (but this should not happen).
        """
        super().full_clean()

        if not self.is_valid_and_matched():
            return

        transformed_data = self.cleaned_data_as_serializer_dict()
        serializer = InteractionSerializer(context={'is_bulk_import': True})

        try:
            serializer.run_validators(transformed_data)
        except serializers.ValidationError as exc:
            # Make sure that errors are wrapped in a dict, and values are always a list
            normalised_errors = serializers.as_serializer_error(exc)

            for field, errors in normalised_errors.items():
                self._add_serializer_error(field, errors)

    @atomic
    def save(self, user, source):
        """Creates an interaction from the cleaned data."""
        serializer_data = self.cleaned_data_as_serializer_dict()

        contacts = serializer_data.pop('contacts')
        dit_participants = serializer_data.pop('dit_participants')
        # Remove `is_event` if it's present as it's a computed field and isn't saved
        # on the model
        serializer_data.pop('is_event', None)

        interaction = Interaction(
            **serializer_data,
            created_by=user,
            modified_by=user,
            source=source,
        )
        interaction.save()

        interaction.contacts.add(*contacts)

        for dit_participant in dit_participants:
            InteractionDITParticipant(
                interaction=interaction,
                **dit_participant,
            ).save()

        return interaction

    def _add_serializer_error(self, field, errors):
        mapped_field = self.SERIALIZER_FIELD_MAPPING.get(field, field)

        if mapped_field in self.fields:
            self.add_error(mapped_field, errors)
        else:
            mapped_errors = [
                join_truthy_strings(field, error, sep=': ')
                for error in errors
            ]
            self.add_error(None, mapped_errors)

    def _populate_adviser(self, data, adviser_field, team_field):
        try:
            data[adviser_field] = _look_up_adviser(
                data.get(adviser_field),
                data.get(team_field),
            )
        except ValidationError as exc:
            self.add_error(adviser_field, exc)

    def _populate_service_answers(self, data):
        """Transform service_answer into service_answers dictionary."""
        service = data.get('service')
        if not service:
            return

        service_answer = data.get('service_answer')

        if not service.interaction_questions.exists():
            if service_answer:
                self.add_error(
                    'service_answer',
                    ValidationError(
                        SERVICE_ANSWER_NOT_REQUIRED,
                        code='service_answer_not_required',
                    ),
                )
            # if service has no questions and answer is not provided, there is nothing to do
            return

        if not service_answer:
            self.add_error(
                'service_answer',
                ValidationError(
                    SERVICE_ANSWER_REQUIRED,
                    code='service_answer_required',
                ),
            )
            return

        try:
            service_answer_option_db = ServiceAnswerOption.objects.get(
                name__iexact=service_answer,
                question__service=service,
            )
            data['service_answers'] = {
                str(service_answer_option_db.question.pk): {
                    str(service_answer_option_db.pk): {},
                },
            }
        except ServiceAnswerOption.DoesNotExist:
            self.add_error(
                'service_answer',
                ValidationError(
                    SERVICE_ANSWER_NOT_FOUND,
                    code='service_answer_not_found',
                ),
            )

    @staticmethod
    def _populate_contact(data):
        """Attempt to look up the contact using the provided email address."""
        contact_email = data.get('contact_email')

        if not contact_email:
            # No contact email address was provided, or it did not pass validation.
            # Skip the look-up in this case.
            return

        data['contact'], data['contact_matching_status'] = find_active_contact_by_email_address(
            contact_email,
        )

    def _check_adviser_1_and_2_are_different(self, data):
        adviser_1 = data.get('adviser_1')
        adviser_2 = data.get('adviser_2')

        if adviser_1 and adviser_1 == adviser_2:
            err = ValidationError(
                ADVISER_2_IS_THE_SAME_AS_ADVISER_1,
                code='adviser_2_is_the_same_as_adviser_1',
            )
            self.add_error('adviser_2', err)

    def _validate_not_duplicate_of_prior_row(self, data):
        if not self.duplicate_tracker:
            return

        if self.duplicate_tracker.has_item(data):
            self.add_error(None, DUPLICATE_OF_ANOTHER_ROW_MESSAGE)
            return

        self.duplicate_tracker.add_item(data)

    def _validate_not_duplicate_of_existing_interaction(self, data):
        if is_duplicate_of_existing_interaction(data):
            self.add_error(None, DUPLICATE_OF_EXISTING_INTERACTION_MESSAGE)

    def cleaned_data_as_serializer_dict(self):
        """
        Transforms cleaned data into a dict suitable for use with the validators from
        InteractionSerializer.
        """
        data = self.cleaned_data

        if not self.is_matched():
            raise DataHubException('Cannot create a serializer dict for an unmatched contact')

        subject = data.get('subject') or data['service'].name
        dit_participants = [
            {
                'adviser': adviser,
                'team': adviser.dit_team,
            }
            for adviser in (data['adviser_1'], data.get('adviser_2'))
            if adviser
        ]

        creation_data = {
            'contacts': [data['contact']],
            'communication_channel': data.get('communication_channel'),
            'company': data['contact'].company,
            'date': datetime.combine(data['date'], time(), tzinfo=utc),
            'dit_participants': dit_participants,
            'event': data.get('event_id'),
            'kind': data['kind'],
            'notes': data.get('notes'),
            'service': data['service'],
            'service_answers': data.get('service_answers'),
            'status': Interaction.STATUSES.complete,
            'subject': subject,
            'theme': data['theme'],
            'was_policy_feedback_provided': False,
        }

        if data['kind'] == Interaction.KINDS.service_delivery:
            creation_data['is_event'] = bool(data.get('event_id'))

        return creation_data


def _look_up_adviser(adviser_name, team):
    if not adviser_name:
        return None

    # Note: An index has been created for this specific look-up (see note on the model).
    # If the filter arguments or name annotation is changed, the index may need to be
    # updated.
    get_kwargs = {
        'is_active': True,
        'name__iexact': adviser_name,
    }

    if team:
        get_kwargs['dit_team'] = team

    queryset = Advisor.objects.annotate(
        name=PreferNullConcat('first_name', Value(' '), 'last_name'),
    )

    try:
        return queryset.get(**get_kwargs)
    except Advisor.DoesNotExist:
        if team:
            raise ValidationError(
                ADVISER_WITH_TEAM_NOT_FOUND_MESSAGE,
                code='adviser_and_team_not_found',
            )

        raise ValidationError(ADVISER_NOT_FOUND_MESSAGE, code='adviser_not_found')
    except Advisor.MultipleObjectsReturned:
        raise ValidationError(MULTIPLE_ADVISERS_FOUND_MESSAGE, code='multiple_advisers_found')
