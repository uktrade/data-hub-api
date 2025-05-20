from rest_framework import serializers

from datahub.company.serializers import NestedRelatedField
from datahub.company_activity.models import PromptPayments


class PromptPaymentsSerializer(serializers.ModelSerializer):
    """Serializer for PromptPayments data."""

    company = NestedRelatedField(
        'company.Company',
        read_only=True,
        extra_fields=('name',),
    )
    contact = NestedRelatedField(
        'company.Contact',
        read_only=True,
        extra_fields=('name', 'email'),
    )

    class Meta:
        model = PromptPayments
        fields = (
            'id',
            'source_id',
            'reporting_period_start_date',
            'reporting_period_end_date',
            'filing_date',
            'company_name',
            'company_house_number',
            'company',
            'email_address',
            'contact',
            'approved_by',
            'qualifying_contracts_in_period',
            'average_paid_days',
            'paid_within_30_days_pct',
            'paid_31_to_60_days_pct',
            'paid_after_61_days_pct',
            'paid_later_than_terms_pct',
            'payment_shortest_period_days',
            'payment_longest_period_days',
            'payment_max_period_days',
            'payment_terms_changed_comment',
            'payment_terms_changed_notified_comment',
            'code_of_practice',
            'other_electronic_invoicing',
            'other_supply_chain_finance',
            'other_retention_charges_in_policy',
            'other_retention_charges_in_past',
            'created_on',
            'modified_on',
        )
        read_only_fields = fields
