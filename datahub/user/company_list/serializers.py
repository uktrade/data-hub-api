from django.utils.translation import gettext_lazy
from rest_framework import serializers

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


class PipelineItemSerializer(serializers.ModelSerializer):
    """Serialiser for pipeline item."""

    default_error_messages = {
        'archived_company': gettext_lazy("An archived company can't be added to the pipeline."),
        'field_cannot_be_updated': gettext_lazy('field not allowed to be update.'),
        'field_cannot_be_empty': gettext_lazy('This field may not be blank.'),
        'field_is_required': gettext_lazy('This field is required.'),
        'contact_company_mismatch': gettext_lazy('Contact does not belong to company.'),
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
    contact = NestedRelatedField(
        Contact,
        extra_fields=('id', 'name'),
        required=False, allow_null=True,
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

    def validate_contact(self, contact):
        """
        Vaidate contact belongs to company
        when its provided.
        """
        if contact and self.instance and contact not in self.instance.company.contacts.all():
            raise serializers.ValidationError(
                self.error_messages['contact_company_mismatch'],
            )
        return contact

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
            if data.get('contact') and data.get('company'):
                if not Contact.objects.filter(
                    id=data.get('contact').id, company__id=data.get('company').id,
                ).exists():
                    raise serializers.ValidationError(
                        {
                            'contact': self.error_messages['contact_company_mismatch'],
                        },
                    )

        if self.partial and self.instance:
            allowed_fields = {
                'status',
                'name',
                'contact',
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

        return data

    class Meta:
        model = PipelineItem
        fields = (
            'id',
            'company',
            'name',
            'status',
            'adviser',
            'created_on',
            'contact',
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
