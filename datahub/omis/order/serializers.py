from django.db import transaction
from django.utils.timezone import now
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from datahub.company.models import Advisor, Company, Contact
from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import DataCombiner, is_blank
from datahub.core.validators import (
    AddressValidator,
    OperatorRule,
    RulesBasedValidator,
    ValidationRule,
)
from datahub.metadata.models import Country, Sector, Team, UKRegion
from datahub.omis.market.models import Market
from datahub.omis.order.constants import OrderStatus, VATStatus
from datahub.omis.order.models import (
    CancellationReason,
    Order,
    OrderAssignee,
    OrderSubscriber,
    ServiceType,
)
from datahub.omis.order.validators import (
    ContactWorksAtCompanyValidator,
    OrderEditableFieldsValidator,
    OrderInStatusRule,
    OrderInStatusValidator,
)


ORDER_FIELDS_INVOICE_RELATED = {
    'billing_address_1',
    'billing_address_2',
    'billing_address_town',
    'billing_address_county',
    'billing_address_postcode',
    'billing_address_country',
    'vat_status',
    'vat_number',
    'vat_verified',
    'po_number',
}


class OrderSerializer(serializers.ModelSerializer):
    """Order DRF serializer"""

    created_by = NestedRelatedField(Advisor, read_only=True)
    modified_by = NestedRelatedField(Advisor, read_only=True)

    company = NestedRelatedField(Company)
    contact = NestedRelatedField(Contact)
    primary_market = NestedRelatedField(Country)
    sector = NestedRelatedField(Sector, required=False, allow_null=True)
    uk_region = NestedRelatedField(UKRegion, required=False, allow_null=True)

    service_types = NestedRelatedField(ServiceType, many=True, required=False)

    description = serializers.CharField(allow_blank=True, required=False)
    contacts_not_to_approach = serializers.CharField(allow_blank=True, required=False)
    further_info = serializers.CharField(allow_blank=True, required=False)
    existing_agents = serializers.CharField(allow_blank=True, required=False)

    delivery_date = serializers.DateField(required=False, allow_null=True)

    billing_address_country = NestedRelatedField(Country, required=False, allow_null=True)

    completed_by = NestedRelatedField(Advisor, read_only=True)

    cancellation_reason = NestedRelatedField(CancellationReason, read_only=True)
    cancelled_by = NestedRelatedField(Advisor, read_only=True)

    default_error_messages = {
        'readonly': gettext_lazy('This field cannot be changed at this stage.'),
    }

    class Meta:
        model = Order
        fields = (
            'id',
            'reference',
            'status',
            'created_on',
            'created_by',
            'modified_on',
            'modified_by',
            'company',
            'contact',
            'primary_market',
            'sector',
            'uk_region',
            'service_types',
            'description',
            'contacts_not_to_approach',
            'contact_email',
            'contact_phone',
            'product_info',
            'further_info',
            'existing_agents',
            'permission_to_approach_contacts',
            'delivery_date',
            'po_number',
            'discount_value',
            'vat_status',
            'vat_number',
            'vat_verified',
            'net_cost',
            'subtotal_cost',
            'vat_cost',
            'total_cost',
            'billing_company_name',
            'billing_contact_name',
            'billing_email',
            'billing_phone',
            'billing_address_1',
            'billing_address_2',
            'billing_address_town',
            'billing_address_county',
            'billing_address_postcode',
            'billing_address_country',
            'archived_documents_url_path',
            'paid_on',
            'completed_by',
            'completed_on',
            'cancelled_by',
            'cancelled_on',
            'cancellation_reason',
        )
        read_only_fields = (
            'id',
            'reference',
            'status',
            'created_on',
            'created_by',
            'modified_on',
            'modified_by',
            'contact_email',
            'contact_phone',
            'product_info',
            'permission_to_approach_contacts',
            'discount_value',
            'net_cost',
            'subtotal_cost',
            'vat_cost',
            'total_cost',
            'archived_documents_url_path',
            'paid_on',
            'completed_by',
            'completed_on',
            'cancelled_by',
            'cancelled_on',
            'cancellation_reason',
            'billing_company_name',
            'billing_contact_name',
            'billing_email',
            'billing_phone',
        )
        validators = (
            # only some of the fields can be changed depending of the status
            OrderEditableFieldsValidator(
                {
                    OrderStatus.draft: {
                        *ORDER_FIELDS_INVOICE_RELATED,
                        'description', 'service_types', 'sector', 'uk_region',
                        'contacts_not_to_approach', 'contact', 'existing_agents',
                        'further_info', 'delivery_date',
                    },
                    OrderStatus.quote_awaiting_acceptance: {
                        *ORDER_FIELDS_INVOICE_RELATED,
                        'contact',
                    },
                    OrderStatus.quote_accepted: {
                        *ORDER_FIELDS_INVOICE_RELATED,
                        'contact',
                    },
                    OrderStatus.paid: {'contact'},
                    OrderStatus.complete: {},  # nothing can be changed
                    OrderStatus.cancelled: {},  # nothing can be changed
                },
            ),
            # contact has to work at company
            ContactWorksAtCompanyValidator(),
            # validate billing address if edited
            AddressValidator(
                lazy=True,
                fields_mapping={
                    'billing_address_1': {'required': True},
                    'billing_address_2': {'required': False},
                    'billing_address_town': {'required': True},
                    'billing_address_county': {'required': False},
                    'billing_address_postcode': {'required': False},
                    'billing_address_country': {'required': True},
                },
            ),
        )

    def validate_service_types(self, service_types):
        """Validates that service types are not disabled."""
        if self.instance:
            created_on = self.instance.created_on
        else:
            created_on = now()

        disabled_service_types = [
            service_type.name
            for service_type in service_types
            if service_type.was_disabled_on(created_on)
        ]

        if disabled_service_types:
            raise serializers.ValidationError(
                f'"{", ".join(disabled_service_types)}" disabled.',
            )

        return service_types

    def validate_primary_market(self, country):
        """Validates that the primary market is not disabled."""
        if self.instance:
            created_on = self.instance.created_on
        else:
            created_on = now()

        try:
            market = Market.objects.get(pk=country)
        except Market.DoesNotExist:
            raise serializers.ValidationError(
                f"The OMIS market for country '{country}' doesn't exist.",
            )
        else:
            if market.was_disabled_on(created_on):
                raise serializers.ValidationError(f'"{country}" disabled.')

        return country

    def _reset_vat_fields_if_necessary(self, data):
        """If vat_status is set and != 'eu', vat_number and vat_verified are reset."""
        data_combiner = DataCombiner(self.instance, data)

        vat_status = data_combiner.get_value('vat_status')
        if vat_status and vat_status != VATStatus.eu:
            data['vat_number'] = ''
            data['vat_verified'] = None

        return data

    def validate(self, data):
        """Add extra logic to the default DRF one."""
        data = self._reset_vat_fields_if_necessary(data)
        return data

    def create(self, validated_data):
        """
        Populate `uk_region` during the order creation if not otherwise specified.
        """
        if 'uk_region' not in validated_data:
            validated_data['uk_region'] = validated_data['company'].uk_region
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update invoice details if any of the invoice related fields has changed.
        """
        with transaction.atomic():
            instance = super().update(instance, validated_data)

            # update invoice details if necessary
            if (
                instance.status == OrderStatus.quote_accepted
                and (ORDER_FIELDS_INVOICE_RELATED & validated_data.keys())
            ):
                instance.update_invoice_details()

            return instance


class CompleteOrderSerializer(OrderSerializer):
    """DRF serializer for marking an order as complete."""

    class Meta:
        model = Order
        fields = ()

    def complete(self):
        """Mark an order as complete."""
        self.instance.complete(
            by=self.context['current_user'],
        )
        return self.instance


class CancelOrderSerializer(OrderSerializer):
    """DRF serializer for cancelling an order."""

    cancellation_reason = NestedRelatedField(CancellationReason)

    class Meta:
        model = Order
        fields = ('cancellation_reason',)

    def cancel(self):
        """Cancel an order."""
        self.instance.cancel(
            by=self.context['current_user'],
            reason=self.validated_data['cancellation_reason'],
        )
        return self.instance


class PublicOrderSerializer(serializers.ModelSerializer):
    """DRF serializer for public facing API."""

    primary_market = NestedRelatedField(Country)
    uk_region = NestedRelatedField(UKRegion)
    company = NestedRelatedField(Company)
    contact = NestedRelatedField(Contact)
    billing_address_country = NestedRelatedField(Country)

    class Meta:
        model = Order
        fields = (
            'public_token',
            'reference',
            'status',
            'created_on',
            'company',
            'contact',
            'primary_market',
            'uk_region',
            'contact_email',
            'contact_phone',
            'vat_status',
            'vat_number',
            'vat_verified',
            'po_number',
            'discount_value',
            'net_cost',
            'subtotal_cost',
            'vat_cost',
            'total_cost',
            'billing_company_name',
            'billing_contact_name',
            'billing_email',
            'billing_phone',
            'billing_address_1',
            'billing_address_2',
            'billing_address_town',
            'billing_address_county',
            'billing_address_postcode',
            'billing_address_country',
            'paid_on',
            'completed_on',
        )
        read_only_fields = fields


def existing_adviser(adviser_id):
    """
    DRF Validator. It raises a ValidationError if adviser_id is not a valid adviser id.
    """
    try:
        Advisor.objects.get(id=adviser_id)
    except Advisor.DoesNotExist:
        raise serializers.ValidationError(f'{adviser_id} is not a valid adviser')
    return adviser_id


class SubscribedAdviserListSerializer(serializers.ListSerializer):
    """DRF List serializer for OrderSubscriber(s)."""

    default_validators = [
        OrderInStatusValidator(
            allowed_statuses=(
                OrderStatus.draft,
                OrderStatus.quote_awaiting_acceptance,
                OrderStatus.quote_accepted,
                OrderStatus.paid,
            ),
        ),
    ]

    def save(self, **kwargs):
        """
        Overrides save as the logic is not the standard DRF one.

        1. if a subscriber is still in the list, don't do anything
        2. if a subscriber was not in the list, add it
        3. if a subscriber is not in the list any more, remove it
        """
        assert hasattr(self, '_errors'), (
            'You must call `.is_valid()` before calling `.save()`.'
        )

        assert not self.errors, (
            'You cannot call `.save()` on a serializer with invalid data.'
        )

        order = self.context['order']
        modified_by = self.context['modified_by']

        current_list = set(order.subscribers.values_list('adviser_id', flat=True))
        final_list = {data['id'] for data in self.validated_data}

        to_delete = current_list - final_list
        to_add = final_list - current_list

        order.subscribers.filter(adviser__in=to_delete).delete()
        for adviser_id in to_add:
            OrderSubscriber.objects.create(
                order=order,
                adviser_id=adviser_id,
                created_by=modified_by,
                modified_by=modified_by,
            )


class TeamWithRegionSerializer(serializers.ModelSerializer):
    """DRF serializer for teams with region."""

    uk_region = NestedRelatedField(Team, read_only=True)

    class Meta:
        model = Team
        fields = (
            'id',
            'name',
            'uk_region',
        )
        read_only_fields = fields


class SubscribedAdviserSerializer(serializers.Serializer):
    """
    DRF serializer for an adviser subscribed to an order.
    """

    id = serializers.UUIDField(validators=[existing_adviser])
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    dit_team = TeamWithRegionSerializer(read_only=True)

    class Meta:
        list_serializer_class = SubscribedAdviserListSerializer


class OrderAssigneeListSerializer(serializers.ListSerializer):
    """DRF List serializer for OrderAssignee(s)."""

    default_validators = [
        OrderInStatusValidator(
            allowed_statuses=(
                OrderStatus.draft,
                OrderStatus.quote_awaiting_acceptance,
                OrderStatus.quote_accepted,
                OrderStatus.paid,
            ),
        ),
    ]

    def validate(self, data):
        """Validate the list of assignees."""
        self.validate_only_one_lead(data)
        self.validate_force_delete(data)
        return data

    def validate_force_delete(self, data):
        """Validate that assignees cannot be deleted if the order.status == paid."""
        order = self.context['order']
        force_delete = self.context['force_delete']

        if order.status != OrderStatus.draft and force_delete:
            raise ValidationError('You cannot delete any assignees at this stage.')
        return data

    def validate_only_one_lead(self, data):
        """
        If the order is in draft, validate that only one assignee can be marked as lead.
        """
        order = self.context['order']
        force_delete = self.context['force_delete']

        if order.status != OrderStatus.draft:
            return

        existing_assignees = dict(order.assignees.values_list('adviser_id', 'is_lead'))

        leads = []
        for assignee_data in data:
            adviser_id = assignee_data['adviser'].id

            try:
                is_lead = assignee_data['is_lead']
            except KeyError:
                # in case of PATCH when the field has not been passed in,
                # get it from the db record instead
                is_lead = existing_assignees.get(adviser_id, False)

            if is_lead:
                leads.append(adviser_id)

            existing_assignees.pop(adviser_id, None)

        # in case of PATCH if not force_delete, you don't have to pass all the elements
        # so we need to check the remaining db records.
        if not force_delete:
            leads += [
                adviser_id
                for adviser_id, is_lead in existing_assignees.items()
                if is_lead
            ]

        if len(leads) > 1:
            raise ValidationError('Only one lead allowed.')
        return data

    def save(self, **kwargs):
        """
        Overrides save as the logic is not the standard DRF one.

        1. if an assignee is not in data and force_delete is True then, assignee is deleted
        2. if the assignee is in data, it gets updated
        3. if data has extra assignees, they get created
        """
        assert hasattr(self, '_errors'), (
            'You must call `.is_valid()` before calling `.save()`.'
        )

        assert not self.errors, (
            'You cannot call `.save()` on a serializer with invalid data.'
        )

        order = self.context['order']
        modified_by = self.context['modified_by']
        force_delete = self.context['force_delete']

        validated_data_dict = {data['adviser'].id: data for data in self.validated_data}
        for assignee in order.assignees.all():
            assignee_adviser_id = assignee.adviser.id

            if assignee_adviser_id not in validated_data_dict:
                # DELETE
                if force_delete:
                    self.child.delete(assignee)
            else:
                # UPDATE
                data = validated_data_dict[assignee_adviser_id]
                data = {
                    field_name: field_value
                    for field_name, field_value in data.items()
                    if getattr(assignee, field_name) != field_value
                }
                if data:  # if something has changed, save
                    data = {
                        **data,
                        'order': order,
                        'modified_by': modified_by,
                    }
                    self.child.update(assignee, data)

                del validated_data_dict[assignee_adviser_id]

        # ADD
        for data in validated_data_dict.values():
            data = {
                **data,
                'order': order,
                'created_by': modified_by,
                'modified_by': modified_by,
            }
            self.child.create(data)


class OrderAssigneeSerializer(serializers.ModelSerializer):
    """DRF serializer for an adviser assigned to an order."""

    adviser = NestedAdviserField(required=True, allow_null=False)
    estimated_time = serializers.IntegerField(required=False, min_value=0)
    actual_time = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    is_lead = serializers.BooleanField(required=False)

    default_error_messages = {
        'readonly': gettext_lazy(
            'This field cannot be changed at this stage.',
        ),
    }

    class Meta:
        list_serializer_class = OrderAssigneeListSerializer
        model = OrderAssignee
        fields = [
            'adviser',
            'estimated_time',
            'actual_time',
            'is_lead',
        ]
        validators = (
            RulesBasedValidator(
                # can't be changed when in draft, quote_awaiting_acceptance or quote_accepted
                ValidationRule(
                    'readonly',
                    OperatorRule('actual_time', is_blank),
                    when=OrderInStatusRule(
                        [
                            OrderStatus.draft,
                            OrderStatus.quote_awaiting_acceptance,
                            OrderStatus.quote_accepted,
                        ],
                    ),
                ),

                # can't be changed when in quote_awaiting_acceptance, quote_accepted or paid
                ValidationRule(
                    'readonly',
                    OperatorRule('estimated_time', is_blank),
                    when=OrderInStatusRule(
                        [
                            OrderStatus.quote_awaiting_acceptance,
                            OrderStatus.quote_accepted,
                            OrderStatus.paid,
                        ],
                    ),
                ),
                # can't be changed when in quote_awaiting_acceptance, quote_accepted or paid
                ValidationRule(
                    'readonly',
                    OperatorRule('is_lead', is_blank),
                    when=OrderInStatusRule(
                        [
                            OrderStatus.quote_awaiting_acceptance,
                            OrderStatus.quote_accepted,
                            OrderStatus.paid,
                        ],
                    ),
                ),
            ),
        )

    def delete(self, instance):
        """Deletes the instance."""
        instance.delete()
