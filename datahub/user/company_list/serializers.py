from django.utils.timezone import now
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.settings import api_settings

from datahub.company.models import Company, Contact
from datahub.core.serializers import NestedRelatedField
from datahub.metadata import models as metadata_models
from datahub.user.company_list.models import CompanyList, CompanyListItem, PipelineItem


class CompanyListSerializer(serializers.ModelSerializer):
    """Serialiser for a company list."""

    # This is an annotation on the query set
    item_count = serializers.ReadOnlyField()

    class Meta:
        model = CompanyList
        fields = (
            'id',
            'item_count',
            'name',
            'created_on',
        )


class CompanyListItemSerializer(serializers.ModelSerializer):
    """Serialiser for company list items."""

    company = NestedRelatedField(
        Company,
        # If this list of fields is changed, update the equivalent list in the QuerySet.only()
        # call in the queryset module
        extra_fields=('archived', 'name', 'trading_names'),
    )
    latest_interaction = serializers.SerializerMethodField()

    def get_latest_interaction(self, obj):
        """
        Construct a latest interaction object from the latest_interaction_id,
        latest_interaction_date and latest_interaction_subject query set annotations.
        """
        if not obj.latest_interaction_id:
            return None

        return {
            'id': obj.latest_interaction_id,
            'created_on': obj.latest_interaction_created_on,
            # For consistency with the main interaction API, only return the date part.
            # See InteractionSerializer for more information
            'date': obj.latest_interaction_date.date(),
            'subject': obj.latest_interaction_subject,
            'dit_participants': obj.latest_interaction_dit_participants or [],
        }

    class Meta:
        model = CompanyListItem
        fields = (
            'company',
            'created_on',
            'latest_interaction',
        )


class _ManyRelatedAsSingleItemField(NestedRelatedField):
    """
    Serialiser field that makes a to-many field behave like a to-one field.

    Use for temporary backwards compatibility when migrating a to-one field to be a to-many field
    (so that a to-one field can be emulated using a to-many field).

    This isn't intended to be used in any other way as if the to-many field contains multiple
    items, only one of them will be returned, and all of them will overwritten on updates.

    TODO Remove this once contact has been removed from pipeline items.
    """

    def run_validation(self, data=serializers.empty):
        """Validate a user-provided value and return the internal value (converted to a list)."""
        validated_value = super().run_validation(data)
        return [validated_value] if validated_value else []

    def to_representation(self, value):
        """Converts a query set to a dict representation of the first item in the query set."""
        if not value.exists():
            return None

        return super().to_representation(value.first())


class PipelineItemSerializer(serializers.ModelSerializer):
    """Serialiser for pipeline item."""

    default_error_messages = {
        'archived_company': gettext_lazy("An archived company can't be added to the pipeline."),
        'field_cannot_be_updated': gettext_lazy('field not allowed to be update.'),
        'field_cannot_be_empty': gettext_lazy('This field may not be blank.'),
        'field_is_required': gettext_lazy('This field is required.'),
        'one_contact_field': gettext_lazy(
            'Only one of contact and contacts should be provided.',
        ),
    }

    company = NestedRelatedField(
        Company,
        # If this list of fields is changed, update the equivalent list in the QuerySet.only()
        # call in the queryset module
        extra_fields=('name', 'turnover', 'export_potential'),
    )
    adviser = serializers.HiddenField(default=serializers.CurrentUserDefault())
    sector = NestedRelatedField(
        metadata_models.Sector,
        extra_fields=('id', 'segment'),
        required=False, allow_null=True,
    )
    contact = _ManyRelatedAsSingleItemField(
        Contact,
        extra_fields=('id', 'name'),
        source='contacts',
        required=False,
        allow_null=True,
    )
    contacts = NestedRelatedField(
        Contact,
        many=True,
        extra_fields=('id', 'name'),
        required=False,
        allow_null=True,
    )

    def validate_company(self, company):
        """Make sure company is not archived"""
        if company.archived:
            raise serializers.ValidationError(
                self.error_messages['archived_company'],
            )

        return company

    def validate_name(self, name):
        """Make sure name is not blank"""
        if not name:
            raise serializers.ValidationError(
                self.error_messages['field_cannot_be_empty'],
            )
        return name

    def to_internal_value(self, data):
        """
        Checks that contact and contacts haven't both been provided.
        Note: On serialisers, to_internal_value() is called before validate().

        TODO Remove once contact removed from the API.
        """
        if 'contact' in data and 'contacts' in data:
            error = {
                api_settings.NON_FIELD_ERRORS_KEY: [
                    self.error_messages['one_contact_field'],
                ],
            }
            raise serializers.ValidationError(error, code='one_contact_field')

        return super().to_internal_value(data)

    def validate(self, data):
        """
        Raise a validation error if:
        - anything else other than allowed fields is updated.
        - name field is empty when editing.
        - contact doesn't belong to the company being added
        """
        if self.instance is None:
            if (data.get('name') in (None, '')):
                raise serializers.ValidationError(
                    self.error_messages['field_is_required'],
                )

        if self.partial and self.instance:
            allowed_fields = {
                'status',
                'name',
                'contact',
                'contacts',
                'sector',
                'potential_value',
                'likelihood_to_win',
                'expected_win_date',
                'archived',
                'archived_on',
                'archived_reason',
            }
            fields = data.keys()
            extra_fields = fields - allowed_fields
            if extra_fields:
                errors = {
                    field: self.error_messages['field_cannot_be_updated']
                    for field in extra_fields
                }
                raise serializers.ValidationError(errors)

        # Ensure that we have backwards compatibility
        # by copying the first contact in `contacts` field
        # to the `contact` field to ensure we support the FE (which only supports
        # a single contact rather than multiple).
        # Once the FE can support multiple contacts we can remove the below.
        # TODO Remove following deprecation period.
        if 'contacts' in data:
            contacts = data['contacts']
            data['contact'] = contacts[0] if contacts else None

        return data

    def update(self, instance, validated_data):
        """
        Update modified_on field with current date time
        during PATCH transactions
        """
        if self.partial and self.instance:
            self.instance.modified_on = now().isoformat()

        return super().update(instance, validated_data)

    class Meta:
        model = PipelineItem
        fields = (
            'id',
            'company',
            'name',
            'status',
            'adviser',
            'created_on',
            'modified_on',
            'contact',
            'contacts',
            'sector',
            'potential_value',
            'likelihood_to_win',
            'expected_win_date',
            'archived',
            'archived_on',
            'archived_reason',
        )
        read_only_fields = (
            'id',
            'adviser',
            'created_on',
        )
