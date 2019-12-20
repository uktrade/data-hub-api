from unittest import mock

import pytest
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from datahub.core.exceptions import APIConflictException
from datahub.omis.order.constants import OrderStatus, VATStatus
from datahub.omis.order.models import Order
from datahub.omis.order.test.factories import (
    OrderFactory,
    OrderWithCancelledQuoteFactory,
    OrderWithOpenQuoteFactory,
)
from datahub.omis.order.validators import (
    AssigneesFilledInSubValidator,
    CancellableOrderSubValidator,
    CompletableOrderSubValidator,
    ContactWorksAtCompanyValidator,
    NoOtherActiveQuoteExistsSubValidator,
    OrderDetailsFilledInSubValidator,
    OrderEditableFieldsValidator,
    OrderInStatusRule,
    OrderInStatusSubValidator,
    OrderInStatusValidator,
    VATSubValidator,
)


class TestContactWorksAtCompanyValidator:
    """Tests for ContactWorksAtCompanyValidator."""

    def test_contact_from_company(self):
        """
        Test that if the contact specified in data works
        at the company specified in data, the validation passes.
        """
        serializer = mock.Mock()
        company = serializer.instance.company
        new_contact = mock.Mock(company=company)

        validator = ContactWorksAtCompanyValidator()
        data = {
            'contact': new_contact,
            'company': company,
        }

        try:
            validator(data, serializer)
        except Exception:
            pytest.fail('Should not raise a validator error.')

    def test_contact_not_from_company(self):
        """
        Test that if the contact specified in data doesn't works
        at the company specified in data, the validation fails.
        """
        serializer = mock.Mock()
        company = serializer.instance.company
        new_contact = mock.Mock()  # doesn't work at `company`

        validator = ContactWorksAtCompanyValidator()
        data = {
            'contact': new_contact,
            'company': company,
        }

        with pytest.raises(ValidationError):
            validator(data, serializer)

    def test_with_different_field_names(self):
        """
        Test that the validation passes when using different field names.
        """
        serializer = mock.Mock()
        company = serializer.instance.company
        new_main_contact = mock.Mock(company=company)

        validator = ContactWorksAtCompanyValidator(
            contact_field='main_contact',
            company_field='main_company',
        )
        data = {
            'main_contact': new_main_contact,
            'main_company': company,
        }

        try:
            validator(data, serializer)
        except Exception:
            pytest.fail('Should not raise a validator error.')


@pytest.mark.django_db
class TestAssigneesFilledInSubValidator:
    """Tests for the AssigneesFilledInSubValidator."""

    def test_no_assignees_fails(self):
        """Test that the validation fails if the order doesn't have any assignees."""
        order = OrderFactory(assignees=[])

        validator = AssigneesFilledInSubValidator()

        with pytest.raises(ValidationError) as exc:
            validator(order=order)

        assert exc.value.detail == {
            'assignees': ['You need to add at least one assignee.'],
        }

    def test_no_lead_assignee_fails(self):
        """Test that the validation fails if there's no lead assignee."""
        order = OrderFactory()
        order.assignees.update(is_lead=False)

        validator = AssigneesFilledInSubValidator()

        with pytest.raises(ValidationError) as exc:
            validator(order=order)

        assert exc.value.detail == {
            'assignee_lead': ['You need to set a lead assignee.'],
        }

    def test_no_estimated_time_fails(self):
        """
        Test that the validation fails if the combined estimated time of the assignees
        is zero.
        """
        order = OrderFactory()
        order.assignees.update(estimated_time=0)

        validator = AssigneesFilledInSubValidator()

        with pytest.raises(ValidationError) as exc:
            validator(order=order)

        assert exc.value.detail == {
            'assignee_time': ['The total estimated time cannot be zero.'],
        }

    def test_non_zero_estimated_time_succeeds(self):
        """
        Test that the validation succeeds if the combined estimated time of the assignees
        is greater than zero.
        """
        order = OrderFactory()
        assert order.assignees.aggregate(sum=Sum('estimated_time'))['sum'] > 0

        validator = AssigneesFilledInSubValidator()

        try:
            validator(order=order)
        except Exception:
            pytest.fail('Should not raise a validator error.')


@pytest.mark.django_db
class TestOrderDetailsFilledInSubValidator:
    """Tests for the OrderDetailsFilledInSubValidator."""

    @pytest.mark.parametrize('values_as_data', (True, False))
    def test_incomplete_order(self, values_as_data):
        """
        Test that an incomplete order doesn't pass the validation.

        Test both scenarios:
        - with fields on the instance (values_as_data=False)
        - with fields as values in the data param (values_as_data=True)
        """
        order_fields = {
            'primary_market': None,
            'description': '',
            'delivery_date': None,
            'vat_status': '',
        }
        order_m2m_fields = {
            'service_types': [],
        }

        if values_as_data:
            order = Order()
            data = {**order_fields, **order_m2m_fields}
        else:
            order = Order(**order_fields)
            for k, v in order_m2m_fields.items():
                getattr(order, k).set(v)
            data = {}

        validator = OrderDetailsFilledInSubValidator()

        with pytest.raises(ValidationError) as exc:
            validator(data=data, order=order)

        all_fields = list(order_fields) + list(order_m2m_fields)
        assert exc.value.detail == {
            **{field: ['This field is required.'] for field in all_fields},
            'assignees': ['You need to add at least one assignee.'],
        }

    @pytest.mark.parametrize('values_as_data', (True, False))
    def test_complete_order(self, values_as_data):
        """
        Test that a complete order passes the validation.

        Test both scenarios:
        - with fields on the instance (values_as_data=False)
        - with fields as values in the data param (values_as_data=True)
        """
        random_values = OrderFactory()  # used only to set up the related props easily

        order_fields = {
            'primary_market': random_values.primary_market,
            'service_types': random_values.service_types.all(),
            'description': random_values.description,
            'delivery_date': random_values.delivery_date,
            'vat_status': random_values.vat_status,
        }
        order = OrderFactory(**(order_fields if not values_as_data else {}))
        data = order_fields if values_as_data else {}

        validator = OrderDetailsFilledInSubValidator()

        try:
            validator(data=data, order=order)
        except Exception:
            pytest.fail('Should not raise a validator error.')

    def test_validation_errors_appended(self):
        """
        Test that if a field gets more than one error during the validation,
        the errors are appended to the same list and not overridden by other validators.
        """
        order = OrderFactory()

        with mock.patch.object(
            OrderDetailsFilledInSubValidator,
            'get_extra_validators',
        ) as get_extra_validators:

            # trigger a second validation error on the same field
            get_extra_validators.return_value = [
                mock.Mock(
                    side_effect=ValidationError({
                        'description': ['A different error...'],
                    }),
                ),
            ]

            validator = OrderDetailsFilledInSubValidator()

            with pytest.raises(ValidationError) as exc:
                validator(
                    data={
                        'description': '',
                    },
                    order=order,
                )

            assert exc.value.detail == {
                'description': [
                    'This field is required.',
                    'A different error...',
                ],
            }


@pytest.mark.django_db
class TestNoOtherActiveQuoteExistsSubValidator:
    """Tests for the NoOtherActiveQuoteExistsSubValidator."""

    def test_with_existing_active_quote(self):
        """Test that if there's already an active quote, the validation fails."""
        order = OrderWithOpenQuoteFactory()

        validator = NoOtherActiveQuoteExistsSubValidator()

        with pytest.raises(APIConflictException):
            validator(order=order)

    def test_without_any_active_quote(self):
        """Test that if there isn't any active quote, the validation passes."""
        order = OrderFactory()

        validator = NoOtherActiveQuoteExistsSubValidator()

        try:
            validator(order=order)
        except Exception:
            pytest.fail('Should not raise a validator error.')

    def test_with_cancelled_quote(self):
        """Test that if there is a cancelled quote, the validation passes."""
        order = OrderWithCancelledQuoteFactory()

        validator = NoOtherActiveQuoteExistsSubValidator()

        try:
            validator(order=order)
        except Exception:
            pytest.fail('Should not raise a validator error.')


@pytest.mark.django_db
class TestOrderInStatusSubValidator:
    """Tests for the OrderInStatusSubValidator."""

    def test_validation_passes(self):
        """
        Test that the validation passes if order.status is one of the allowed statuses.
        """
        order = OrderFactory(status=OrderStatus.complete)

        validator = OrderInStatusSubValidator(
            allowed_statuses=(
                OrderStatus.draft,
                OrderStatus.complete,
                OrderStatus.cancelled,
            ),
        )

        try:
            validator(order=order)
        except Exception:
            pytest.fail('Should not raise a validator error.')

    def test_validation_fails(self):
        """
        Test that the validation fails if order.status is NOT one of the allowed statuses.
        """
        order = OrderFactory(status=OrderStatus.complete)

        validator = OrderInStatusSubValidator(
            allowed_statuses=(
                OrderStatus.draft,
                OrderStatus.cancelled,
            ),
        )

        with pytest.raises(APIConflictException):
            validator(order=order)

    def test_order_not_required(self):
        """
        Test that if order_required == False and the order passed in is None,
        the validation passes.
        """
        validator = OrderInStatusSubValidator(
            allowed_statuses=(
                OrderStatus.draft,
                OrderStatus.complete,
                OrderStatus.cancelled,
            ),
            order_required=False,
        )

        try:
            validator()
        except Exception:
            pytest.fail('Should not raise a validator error.')


@pytest.mark.django_db
class TestOrderInStatusValidator:
    """Tests for the OrderInStatusValidator."""

    @pytest.mark.parametrize(
        'serializer_factory',
        (
            lambda order: mock.Mock(instance=order, context={}),
            lambda order: mock.Mock(context={'order': order}),
        ),
    )
    def test_validation_passes(self, serializer_factory):
        """
        Test that the validation passes if order.status is one of the allowed statuses.
        """
        order = OrderFactory(status=OrderStatus.complete)

        validator = OrderInStatusValidator(
            allowed_statuses=(
                OrderStatus.draft,
                OrderStatus.complete,
                OrderStatus.cancelled,
            ),
        )
        serializer = serializer_factory(order)

        try:
            validator({}, serializer)
        except Exception:
            pytest.fail('Should not raise a validator error.')

    @pytest.mark.parametrize(
        'serializer_factory',
        (
            lambda order: mock.Mock(instance=order, context={}),
            lambda order: mock.Mock(context={'order': order}),
        ),
    )
    def test_validation_fails(self, serializer_factory):
        """
        Test that the validation fails if order.status is NOT one of the allowed statuses.
        """
        order = OrderFactory(status=OrderStatus.complete)

        validator = OrderInStatusValidator(
            allowed_statuses=(
                OrderStatus.draft,
                OrderStatus.cancelled,
            ),
        )
        serializer = serializer_factory(order)

        with pytest.raises(APIConflictException):
            validator({}, serializer)

    def test_order_not_required(self):
        """
        Test that if order_required == False and the order passed in is None,
        the validation passes.
        """
        validator = OrderInStatusValidator(
            allowed_statuses=(
                OrderStatus.draft,
                OrderStatus.complete,
                OrderStatus.cancelled,
            ),
            order_required=False,
        )
        serializer = mock.Mock(instance=None, context={})

        try:
            validator({}, serializer)
        except Exception:
            pytest.fail('Should not raise a validator error.')


class TestVATSubValidator:
    """Tests for the VATSubValidator."""

    @pytest.mark.parametrize('values_as_data', (True, False))
    def test_nothing_specified_fails(self, values_as_data):
        """
        Test that if none of the vat fields are specified, it raises a ValidationError.

        Test both scenarios:
        - with fields on the instance (values_as_data=False)
        - with fields as values in the data param (values_as_data=True)
        """
        order_fields = {
            'vat_status': '',
            'vat_number': '',
            'vat_verified': None,
        }

        order = Order(**(order_fields if not values_as_data else {}))
        data = order_fields if values_as_data else {}

        validator = VATSubValidator()

        with pytest.raises(ValidationError) as exc:
            validator(data=data, order=order)
        assert exc.value.detail == {'vat_status': ['This field is required.']}

    @pytest.mark.parametrize('values_as_data', (True, False))
    def test_only_status_eu_specified_fails(self, values_as_data):
        """
        Test that if only vat_status = eu is specified, it raises a ValidationError
        as vat_verified (true or false) has to be specified as well.

        Test both scenarios:
        - with fields on the instance (values_as_data=False)
        - with fields as values in the data param (values_as_data=True)
        """
        order_fields = {
            'vat_status': VATStatus.eu,
            'vat_number': '',
            'vat_verified': None,
        }

        order = Order(**(order_fields if not values_as_data else {}))
        data = order_fields if values_as_data else {}

        validator = VATSubValidator()

        with pytest.raises(ValidationError) as exc:
            validator(data=data, order=order)
        assert exc.value.detail == {'vat_verified': ['This field is required.']}

    @pytest.mark.parametrize('values_as_data', (True, False))
    def test_only_status_eu_verified_true_specified_fails(self, values_as_data):
        """
        Test that if vat_status = eu and vat_verified = True but vat_number is not specified,
        it raises a ValidationError.

        Test both scenarios:
        - with fields on the instance (values_as_data=False)
        - with fields as values in the data param (values_as_data=True)
        """
        order_fields = {
            'vat_status': VATStatus.eu,
            'vat_number': '',
            'vat_verified': True,
        }

        order = Order(**(order_fields if not values_as_data else {}))
        data = order_fields if values_as_data else {}

        validator = VATSubValidator()

        with pytest.raises(ValidationError) as exc:
            validator(data=data, order=order)
        assert exc.value.detail == {'vat_number': ['This field is required.']}

    @pytest.mark.parametrize('values_as_data', (True, False))
    def test_complete_verified_eu_vat_succeeds(self, values_as_data):
        """
        Test that if vat_status = eu, vat_verified = True and vat_number is specified,
        the validation passes.

        Test both scenarios:
        - with fields on the instance (values_as_data=False)
        - with fields as values in the data param (values_as_data=True)
        """
        order_fields = {
            'vat_status': VATStatus.eu,
            'vat_number': '0123456789',
            'vat_verified': True,
        }

        order = Order(**(order_fields if not values_as_data else {}))
        data = order_fields if values_as_data else {}

        validator = VATSubValidator()

        try:
            validator(data=data, order=order)
        except Exception:
            pytest.fail('Should not raise a validator error.')

    @pytest.mark.parametrize('values_as_data', (True, False))
    def test_only_status_eu_verified_false_specified_succeeds(self, values_as_data):
        """
        Test that if vat_status = eu, vat_verified = False and vat_number is not specified,
        the validation passes and vat_number is not required when vat_verified is False.

        Test both scenarios:
        - with fields on the instance (values_as_data=False)
        - with fields as values in the data param (values_as_data=True)
        """
        order_fields = {
            'vat_status': VATStatus.eu,
            'vat_number': '',
            'vat_verified': False,
        }

        order = Order(**(order_fields if not values_as_data else {}))
        data = order_fields if values_as_data else {}

        validator = VATSubValidator()

        try:
            validator(data=data, order=order)
        except Exception:
            pytest.fail('Should not raise a validator error.')

    @pytest.mark.parametrize('values_as_data', (True, False))
    @pytest.mark.parametrize('vat_status', (VATStatus.outside_eu, VATStatus.uk))
    def test_only_status_non_eu_succeeds(self, values_as_data, vat_status):
        """
        Test that if vat_status != eu, the validation passes even if the other
        fields are empty.

        Test both scenarios:
        - with fields on the instance (values_as_data=False)
        - with fields as values in the data param (values_as_data=True)
        """
        order_fields = {
            'vat_status': vat_status,
            'vat_number': '',
            'vat_verified': None,
        }

        order = Order(**(order_fields if not values_as_data else {}))
        data = order_fields if values_as_data else {}

        validator = VATSubValidator()

        try:
            validator(data=data, order=order)
        except Exception:
            pytest.fail('Should not raise a validator error.')


class TestCompletableOrderSubValidator:
    """Tests for the CompletableOrderSubValidator."""

    def test_ok_with_all_actual_time_fields_set(self):
        """
        Test that the validation succeeds when all assignee.actual_time fields are set.
        """
        order = mock.MagicMock()
        order.assignees.all.return_value = (
            mock.MagicMock(actual_time=100), mock.MagicMock(actual_time=0),
        )
        validator = CompletableOrderSubValidator()

        try:
            validator(order=order)
        except Exception:
            pytest.fail('Should not raise a validator error.')

    def test_fails_if_not_all_actual_time_fields_set(self):
        """
        Test that the validation fails if not all assignee.actual_time fields are set.
        """
        order = mock.MagicMock()
        order.assignees.all.return_value = (
            mock.MagicMock(actual_time=100), mock.MagicMock(actual_time=None),
        )
        validator = CompletableOrderSubValidator()

        with pytest.raises(ValidationError) as exc:
            validator(order=order)

        assert exc.value.detail == {
            'non_field_errors': (
                'You must set the actual time for all assignees '
                'to complete this order.'
            ),
        }


class TestCancellableOrderSubValidator:
    """Tests for the CancellableOrderSubValidator."""

    @pytest.mark.parametrize(
        'order_status,force,should_pass',
        (
            # with force=False
            (OrderStatus.draft, False, True),
            (OrderStatus.quote_awaiting_acceptance, False, True),
            (OrderStatus.quote_accepted, False, False),
            (OrderStatus.paid, False, False),
            (OrderStatus.complete, False, False),
            (OrderStatus.cancelled, False, False),

            # with force=True
            (OrderStatus.draft, True, True),
            (OrderStatus.quote_awaiting_acceptance, True, True),
            (OrderStatus.quote_accepted, True, True),
            (OrderStatus.paid, True, True),
            (OrderStatus.complete, True, False),
            (OrderStatus.cancelled, True, False),
        ),
    )
    def test_validation(self, order_status, force, should_pass):
        """Test the validator with different order status and force values."""
        order = Order(status=order_status)

        validator = CancellableOrderSubValidator(force=force)

        if should_pass:
            validator(order=order)
        else:
            with pytest.raises(APIConflictException):
                validator(order=order)


@pytest.mark.parametrize(
    'order_status,expected_status,res',
    (
        (OrderStatus.draft, OrderStatus.draft, True),
        (OrderStatus.draft, OrderStatus.paid, False),
    ),
)
def test_order_in_status_rule(order_status, expected_status, res):
    """Tests for OrderInStatusRule."""
    order = mock.Mock(status=order_status)
    combiner = mock.Mock()
    combiner.serializer.context = {'order': order}

    rule = OrderInStatusRule(expected_status)
    assert rule(combiner) == res


class TestOrderEditableFieldsValidator:
    """Tests for the OrderEditableFieldsValidator."""

    @pytest.mark.parametrize(
        'order_status,mapping,data,should_pass',
        (
            # allowed field => OK
            (
                OrderStatus.draft,
                {OrderStatus.draft: {'description'}},
                {'description': 'lorem ipsum'},
                True,
            ),
            # disallowed field => Fail
            (
                OrderStatus.draft,
                {OrderStatus.draft: {'contact'}},
                {'description': 'lorem ipsum'},
                False,
            ),
            # status not in mapping => OK
            (
                OrderStatus.draft,
                {OrderStatus.paid: {'contact'}},
                {'description': 'lorem ipsum'},
                True,
            ),
            # disallowed field didn't change => OK
            (
                OrderStatus.draft,
                {OrderStatus.draft: {'contact'}},
                {'description': 'original description'},
                True,
            ),
            # nothing allowed => Fail
            (
                OrderStatus.draft,
                {OrderStatus.draft: {}},
                {'description': 'lorem ipsum'},
                False,
            ),
        ),
    )
    def test_validation_with_order(self, order_status, mapping, data, should_pass):
        """Test the validator with different order status, mapping and data."""
        order = Order(
            status=order_status,
            description='original description',
        )
        serializer = mock.Mock(instance=order)

        validator = OrderEditableFieldsValidator(mapping)

        if should_pass:
            validator(data, serializer)
        else:
            with pytest.raises(ValidationError):
                validator(data, serializer)

    def test_validation_passes_on_creation(self):
        """Test that the validation passes if we are creating the order instead of editing it."""
        serializer = mock.Mock(instance=None)

        validator = OrderEditableFieldsValidator({OrderStatus.paid: {'contact'}})
        validator({'description': 'lorem ipsum'}, serializer)
