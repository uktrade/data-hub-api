from django.utils.timezone import now

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from datahub.company.models import Advisor, Company, Contact
from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import ConstantModelSerializer, NestedRelatedField
from datahub.core.validate_utils import DataCombiner
from datahub.metadata.models import Country, Sector, Team

from .models import Order, OrderAssignee, OrderSubscriber, ServiceType


class ServiceTypeSerializer(ConstantModelSerializer):
    """Service Type DRF serializer"""

    disabled_on = serializers.ReadOnlyField()


class OrderSerializer(serializers.ModelSerializer):
    """Order DRF serializer"""

    id = serializers.UUIDField(read_only=True)
    reference = serializers.CharField(read_only=True)

    created_on = serializers.DateTimeField(read_only=True)
    created_by = NestedRelatedField(Advisor, read_only=True)
    modified_on = serializers.DateTimeField(read_only=True)
    modified_by = NestedRelatedField(Advisor, read_only=True)

    company = NestedRelatedField(Company)
    contact = NestedRelatedField(Contact)
    primary_market = NestedRelatedField(Country)
    sector = NestedRelatedField(Sector, required=False, allow_null=True)

    service_types = NestedRelatedField(ServiceType, many=True, required=False)

    description = serializers.CharField(allow_blank=True, required=False)
    contacts_not_to_approach = serializers.CharField(allow_blank=True, required=False)

    delivery_date = serializers.DateField(required=False, allow_null=True)

    # legacy fields
    product_info = serializers.CharField(read_only=True)
    further_info = serializers.CharField(read_only=True)
    existing_agents = serializers.CharField(read_only=True)
    permission_to_approach_contacts = serializers.CharField(read_only=True)

    class Meta:  # noqa: D101
        model = Order
        fields = [
            'id',
            'reference',
            'created_on',
            'created_by',
            'modified_on',
            'modified_by',
            'company',
            'contact',
            'primary_market',
            'sector',
            'service_types',
            'description',
            'contacts_not_to_approach',
            'product_info',
            'further_info',
            'existing_agents',
            'permission_to_approach_contacts',
            'delivery_date',
        ]

    def validate(self, data):
        """Extra checks."""
        data_combiner = DataCombiner(self.instance, data)
        company = data_combiner.get_value('company')
        contact = data_combiner.get_value('contact')

        # check that contact works at company
        if contact.company != company:
            raise serializers.ValidationError({
                'contact': 'The contact does not work at the given company.'
            })

        # company and primary_market cannot be changed after creation
        if self.instance:
            if company != self.instance.company:
                raise serializers.ValidationError({
                    'company': 'The company cannot be changed after creation.'
                })

            if data_combiner.get_value('primary_market') != self.instance.primary_market:
                raise serializers.ValidationError({
                    'primary_market': 'The primary market cannot be changed after creation.'
                })

        # cannot use a disabled service types
        if 'service_types' in data:
            if self.instance:
                created_on = self.instance.created_on
            else:
                created_on = now()

            disabled_service_types = [
                service_type.name
                for service_type in data['service_types']
                if service_type.was_disabled_on(created_on)
            ]

            if disabled_service_types:
                raise serializers.ValidationError({
                    'service_types': f'"{", ".join(disabled_service_types)}" disabled.'
                })

        return data


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
                modified_by=modified_by
            )


class SubscribedAdviserSerializer(serializers.Serializer):
    """
    DRF serializer for an adviser subscribed to an order.
    """

    id = serializers.UUIDField(validators=[existing_adviser])
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    dit_team = NestedRelatedField(Team, read_only=True)

    class Meta:  # noqa: D101
        list_serializer_class = SubscribedAdviserListSerializer


class OrderAssigneeListSerializer(serializers.ListSerializer):
    """DRF List serializer for OrderAssignee(s)."""

    def validate(self, data):
        """Validates the list of assignees."""
        self.validate_only_one_lead(data)
        return data

    def validate_only_one_lead(self, data):
        """Validates that only one assignee can be marked as lead."""
        order = self.context['order']
        force_delete = self.context['force_delete']

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
                        'modified_by': modified_by
                    }
                    self.child.update(assignee, data)

                del validated_data_dict[assignee_adviser_id]

        # ADD
        for assignee_adviser_id, data in validated_data_dict.items():
            data = {
                **data,
                'order': order,
                'created_by': modified_by,
                'modified_by': modified_by
            }
            self.child.create(data)


class OrderAssigneeSerializer(serializers.ModelSerializer):
    """DRF serializer for an adviser assigned to an order."""

    adviser = NestedAdviserField(required=True, allow_null=False)
    estimated_time = serializers.IntegerField(required=False)
    is_lead = serializers.BooleanField(required=False)

    class Meta:  # noqa: D101
        list_serializer_class = OrderAssigneeListSerializer
        model = OrderAssignee
        fields = [
            'adviser',
            'estimated_time',
            'is_lead',
        ]

    def delete(self, instance):
        """Deletes the instance."""
        instance.delete()
