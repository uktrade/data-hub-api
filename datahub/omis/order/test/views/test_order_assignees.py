import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.models import OrderAssignee
from datahub.omis.order.test.factories import OrderAssigneeFactory, OrderFactory, OrderPaidFactory
from datahub.omis.order.views import AssigneeView

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestGetOrderAssignees(APITestMixin):
    """Tests related to getting the list of advisers assigned to an order."""

    def test_access_is_denied_if_without_permissions(self):
        """Test that a 403 is returned if the user has no permissions."""
        order = OrderFactory()
        user = create_test_user()
        api_client = self.create_api_client(user=user)
        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )

        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_access_allowed_if_with_view_permission(self):
        """Test that a 200 is returned if the user has the view permission."""
        order = OrderFactory()
        user = create_test_user(permission_codenames=['view_orderassignee'])
        api_client = self.create_api_client(user=user)
        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )

        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_empty(self):
        """Test that calling GET returns [] if no-one is assigned."""
        order = OrderFactory(assignees=[])

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_non_empty(self):
        """
        Test that calling GET returns the list of advisers assigned to the order.
        """
        advisers = AdviserFactory.create_batch(3)
        order = OrderFactory(assignees=[])
        for i, adviser in enumerate(advisers[:2]):
            OrderAssigneeFactory(
                order=order,
                adviser=adviser,
                estimated_time=(120 * i),
            )

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'adviser': {
                    'id': str(adviser.id),
                    'first_name': adviser.first_name,
                    'last_name': adviser.last_name,
                    'name': adviser.name,
                },
                'estimated_time': (120 * i),
                'actual_time': None,
                'is_lead': False,
            }
            for i, adviser in enumerate(advisers[:2])
        ]

    def test_invalid_order(self):
        """Test that calling GET on an invalid order returns 404."""
        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': '00000000-0000-0000-0000-000000000000'},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestChangeAssigneesPermissions(APITestMixin):
    """Permission-related tests for changing order assignees."""

    def test_access_is_denied_if_without_permissions(self):
        """Test that a 403 is returned if the user has no permissions."""
        order = OrderFactory()

        user = create_test_user()
        api_client = self.create_api_client(user=user)
        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = api_client.patch(url, data=[])

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_access_allowed_if_with_change_permission(self):
        """Test that a 200 is returned if the user has the change permission."""
        order = OrderFactory()

        user = create_test_user(permission_codenames=['change_orderassignee'])
        api_client = self.create_api_client(user=user)
        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = api_client.patch(url, data=[])

        assert response.status_code == status.HTTP_200_OK


class TestChangeAssigneesWhenOrderInDraft(APITestMixin):
    """
    Tests related to changing who is assigned to an order when the order is in draft.

    - assignees can be added, removed and partially changed
    - only `estimated_time` and `is_lead` can be set/changed
    - `actual_time` cannot be set at this stage
    """

    def test_ok_if_assignee_added_or_changed(self):
        """
        Test that assignees can be added and/or changed.
        Given an order with the following assignees:
            [
                {
                    "adviser": {
                        "id": 1,
                        "first_name": "Joe",
                        "last_name": "Doe"
                    },
                    "estimated_time": 100,
                    "is_lead": true
                },
                {
                    "adviser": {
                        "id": 2,
                        "first_name": "Rebecca",
                        "last_name": "Bah"
                    },
                    "estimated_time": 250,
                    "is_lead": false
                },
            ]

        if I pass the following data:
            [
                {
                    "adviser": {"id": 1},
                    "estimated_time": 200,
                    "is_lead": false
                },
                {
                    "adviser": {"id": 3},
                    "estimated_time": 250,
                    "is_lead": true
                },
            ]

        then:
            1. adviser 1 gets updated
                - estimated_time from 100 to 200
                - is_lead from true to false
            2. adviser 2 doesn't change
            3. adviser 3 gets added
        """
        created_by = AdviserFactory()
        order = OrderFactory(assignees=[])
        adviser1 = AdviserFactory()
        adviser2 = AdviserFactory()
        adviser3 = AdviserFactory()

        assignee1 = OrderAssigneeFactory(
            order=order, adviser=adviser1, estimated_time=100, is_lead=True,
            created_by=created_by, modified_by=created_by,
        )
        assignee2 = OrderAssigneeFactory(
            order=order, adviser=adviser2, estimated_time=250, is_lead=False,
            created_by=created_by, modified_by=created_by,
        )

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser': {'id': adviser1.id},
                    'estimated_time': 200,
                    'is_lead': False,
                },
                {
                    'adviser': {'id': adviser3.id},
                    'estimated_time': 250,
                    'is_lead': True,
                },
            ],
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'adviser': {
                    'id': str(adviser1.id),
                    'first_name': adviser1.first_name,
                    'last_name': adviser1.last_name,
                    'name': adviser1.name,
                },
                'estimated_time': 200,
                'actual_time': None,
                'is_lead': False,
            },
            {
                'adviser': {
                    'id': str(adviser2.id),
                    'first_name': adviser2.first_name,
                    'last_name': adviser2.last_name,
                    'name': adviser2.name,
                },
                'estimated_time': assignee2.estimated_time,
                'actual_time': None,
                'is_lead': False,
            },
            {
                'adviser': {
                    'id': str(adviser3.id),
                    'first_name': adviser3.first_name,
                    'last_name': adviser3.last_name,
                    'name': adviser3.name,
                },
                'estimated_time': 250,
                'actual_time': None,
                'is_lead': True,
            },
        ]

        # check created_by / modified_by
        assignee1.refresh_from_db()
        assignee2.refresh_from_db()
        assignee3 = OrderAssignee.objects.get(order=order, adviser=adviser3)

        # 1 = changed
        assert assignee1.created_by == created_by
        assert assignee1.modified_by == self.user

        # 2 = not changed
        assert assignee2.created_by == created_by
        assert assignee2.modified_by == created_by

        # 3 = added
        assert assignee3.created_by == self.user
        assert assignee3.modified_by == self.user

    def test_ok_if_assignee_removed(self):
        """
        Test that assignees can be removed passing the `force_delete` flag.
        Given an order with the following assignees:
            [
                {
                    "adviser": {
                        "id": 1,
                        "first_name": "Joe",
                        "last_name": "Doe"
                    },
                    "estimated_time": 100,
                    "is_lead": true
                },
                {
                    "adviser": {
                        "id": 2,
                        "first_name": "Rebecca",
                        "last_name": "Bah"
                    },
                    "estimated_time": 250,
                    "is_lead": false
                },
            ]

        if I pass the following data with force_delete True:
            [
                {
                    "adviser": {"id": 1},
                    "estimated_time": 200
                },
                {
                    "adviser": {"id": 3},
                    "estimated_time": 250
                },
            ]

        then:
            adviser 2 gets removed
        """
        order = OrderFactory()
        adviser1 = AdviserFactory()
        adviser2 = AdviserFactory()
        adviser3 = AdviserFactory()

        OrderAssigneeFactory(order=order, adviser=adviser1)
        OrderAssigneeFactory(order=order, adviser=adviser2)

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            f'{url}?{AssigneeView.FORCE_DELETE_PARAM}=1',
            [
                {
                    'adviser': {'id': adviser1.id},
                    'estimated_time': 200,
                },
                {
                    'adviser': {'id': adviser3.id},
                    'estimated_time': 250,
                },
            ],
        )

        assert response.status_code == status.HTTP_200_OK
        returned_advisers = {item['adviser']['id'] for item in response.json()}
        assert returned_advisers == {str(adviser1.id), str(adviser3.id)}

    def test_without_changing_any_values(self):
        """
        Test that if I patch an assignee without changing any values,
        the db record doesn't get changed (and therefore modified_by stays the same).
        Given an order with the following assignees:
            [
                {
                    "adviser": {
                        "id": 1,
                        "first_name": "Joe",
                        "last_name": "Doe"
                    },
                    "estimated_time": 100,
                    "is_lead": true
                },
                {
                    "adviser": {
                        "id": 2,
                        "first_name": "Rebecca",
                        "last_name": "Bah"
                    },
                    "estimated_time": 250,
                    "is_lead": false
                },
            ]

        if I pass the following data:
            [
                {
                    "adviser": {"id": 1},
                    "estimated_time": 100,
                    "is_lead": true
                },
            ]

        then:
            adviser 1 doesn't get changed
        """
        created_by = AdviserFactory()
        order = OrderFactory()
        adviser1 = AdviserFactory()
        adviser2 = AdviserFactory()

        assignee1 = OrderAssigneeFactory(
            order=order, adviser=adviser1,
            created_by=created_by, modified_by=created_by,
        )
        OrderAssigneeFactory(order=order, adviser=adviser2)

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser': {'id': adviser1.id},
                    'estimated_time': assignee1.estimated_time,
                    'is_lead': assignee1.is_lead,
                },
            ],
        )

        assert response.status_code == status.HTTP_200_OK
        assignee1.refresh_from_db()

        assert assignee1.created_by == created_by
        assert assignee1.modified_by == created_by

    def test_400_doesnt_commit_changes(self):
        """
        Test that in case of errors, changes are not saved.
        Given an order with the following assignees:
            [
                {
                    "adviser": {
                        "id": 1,
                        "first_name": "Joe",
                        "last_name": "Doe"
                    },
                    "estimated_time": 100,
                    "is_lead": true
                },
                {
                    "adviser": {
                        "id": 2,
                        "first_name": "Rebecca",
                        "last_name": "Bah"
                    },
                    "estimated_time": 250,
                    "is_lead": false
                },
            ]

        if I pass the following data:
            [
                {
                    "adviser": {"id": 1},
                    "estimated_time": 200
                },
                {
                    "adviser": {"id": 3},
                    "estimated_time": 250
                },
                {
                    "adviser": {"id": non-existent},
                    "estimated_time": 250
                },
            ]

        then:
            1. the response returns a validation error as the new adviser doesn't exist
            2. adviser 1 doesn't get updated
            3. adviser 3 doesn't get added
        """
        order = OrderFactory(assignees=[])
        adviser1 = AdviserFactory()
        adviser2 = AdviserFactory()
        adviser3 = AdviserFactory()

        OrderAssigneeFactory(order=order, adviser=adviser1, estimated_time=100, is_lead=True)
        OrderAssigneeFactory(order=order, adviser=adviser2, estimated_time=250, is_lead=False)

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser': {'id': adviser1.id},
                    'estimated_time': 200,
                    'is_lead': False,
                },
                {
                    'adviser': {'id': adviser3.id},
                    'estimated_time': 250,
                    'is_lead': True,
                },
                {
                    'adviser': {'id': '00000000-0000-0000-0000-000000000000'},
                    'estimated_time': 300,
                },
            ],
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {},
            {},
            {
                'adviser': [
                    'Invalid pk "00000000-0000-0000-0000-000000000000" - object does not exist.',
                ],
            },
        ]

        # check db consistency
        adviser1.refresh_from_db()
        adviser2.refresh_from_db()

        qs = order.assignees
        ad_ids = set(qs.values_list('adviser_id', flat=True))
        assert ad_ids == {adviser1.id, adviser2.id}

        assignee1 = qs.get(adviser_id=adviser1.id)
        assert assignee1.estimated_time == 100
        assert assignee1.is_lead

    def test_400_if_readonly_fields_changed(self):
        """
        Test that the `actual_time` field cannot be set when the order is in draft.
        """
        order = OrderFactory(assignees=[])
        OrderAssigneeFactory(order=order, estimated_time=100, is_lead=True)
        assignee2 = OrderAssigneeFactory(order=order, estimated_time=250, is_lead=False)

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser': {'id': assignee2.adviser.id},
                    'actual_time': 200,
                },
            ],
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {
                'actual_time': [
                    'This field cannot be changed at this stage.',
                ],
            },
        ]

    def test_only_one_lead_allowed(self):
        """
        Test that only one lead is allowed and you have to set the old lead to False
        if you want to promote a different adviser.

        Given an order with the following assignees:
            [
                {
                    "adviser": {"id": 1},
                    ...
                    "is_lead": true
                },
                {
                    "adviser": {"id": 2},
                    ...
                    "is_lead": false
                },
                {
                    "adviser": {"id": 3},
                    ...
                    "is_lead": false
                },
            ]

        if I pass the following data:
            [
                {
                    "adviser": {"id": 2},
                    "is_lead": true
                },
                {
                    "adviser": {"id": 3},
                    "estimated_time": 0
                },
                {
                    "adviser": {"id": 4},
                    "estimated_time": 0
                },
            ]

        then:
            the response returns a validation error as adviser 1 and 2 are both marked as lead.
        """
        order = OrderFactory()
        adviser1 = AdviserFactory()
        adviser2 = AdviserFactory()
        adviser3 = AdviserFactory()
        adviser4 = AdviserFactory()

        OrderAssigneeFactory(order=order, adviser=adviser1, estimated_time=100, is_lead=True)
        OrderAssigneeFactory(order=order, adviser=adviser2, estimated_time=250, is_lead=False)
        OrderAssigneeFactory(order=order, adviser=adviser3, estimated_time=300, is_lead=False)

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser': {'id': adviser2.id},
                    'is_lead': True,
                },
                {
                    'adviser': {'id': adviser3.id},
                    'estimated_time': 0,
                },
                {
                    'adviser': {'id': adviser4.id},
                    'estimated_time': 0,
                },
            ],
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'non_field_errors': ['Only one lead allowed.']}

    @pytest.mark.parametrize(
        'disallowed_status', (
            OrderStatus.COMPLETE,
            OrderStatus.CANCELLED,
        ),
    )
    def test_409_if_order_not_in_allowed_status(self, disallowed_status):
        """
        Test that if the order is not in one of the allowed statuses, the endpoint
        returns 409.
        """
        order = OrderFactory(status=disallowed_status)

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            url,
            [{
                'adviser': {'id': AdviserFactory().id},
            }],
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {
            'detail': (
                'The action cannot be performed '
                f'in the current status {disallowed_status.label}.'
            ),
        }


class TestChangeAssigneesWhenOrderInPaid(APITestMixin):
    """
    Tests related to changing order assignees when order is paid.

    - assignees can be added
    - assignees cannot be removed
    - `estimated_time` and `is_lead` cannot be changed
    - only `actual_time` can be set at this stage
    """

    def test_ok_if_assignee_added(self):
        """
        Test that assignees can be added.
        Given an order with the following assignees:
            [
                {
                    "adviser": {"id": 1},
                    "estimated_time": 100,
                    "is_lead": true
                },
                {
                    "adviser": {"id": 2},
                    "estimated_time": 250,
                    "is_lead": false
                },
            ]

        if I pass the following data:
            [
                {
                    "adviser": {"id": 3},
                    "actual_time": 100
                },
            ]

        then:
            the adviser is added.
        """
        order = OrderPaidFactory()
        new_adviser = AdviserFactory()

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser': {'id': new_adviser.id},
                    'actual_time': 100,
                },
            ],
        )

        assert response.status_code == status.HTTP_200_OK
        assert str(new_adviser.id) in [item['adviser']['id'] for item in response.json()]

    def test_400_if_assignee_deleted(self):
        """
        Test that assignees cannot be deleted at this stage.
        Given an order with the following assignees:
            [
                {
                    "adviser": {"id": 1},
                    "estimated_time": 100,
                    "is_lead": true
                },
                {
                    "adviser": {"id": 2},
                    "estimated_time": 250,
                    "is_lead": false
                },
            ]

        if I pass the following data with force_delete == True
            [
                {
                    "adviser": {"id": 1},
                },
            ]

        then:
            the response returns a validation error as no assignee can be deleted.
        """
        order = OrderPaidFactory(assignees=[])
        assignee = OrderAssigneeFactory(order=order)

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            f'{url}?{AssigneeView.FORCE_DELETE_PARAM}=1',
            [
                {
                    'adviser': {'id': assignee.adviser.id},
                },
            ],
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'non_field_errors': [
                'You cannot delete any assignees at this stage.',
            ],
        }

    def test_set_actual_time(self):
        """
        Test that actual_time for any assignee can be set.
        Given an order with the following assignees:
            [
                {
                    "adviser": {"id": 1},
                    "estimated_time": 100,
                    "is_lead": true
                },
                {
                    "adviser": {"id": 2},
                    "estimated_time": 250,
                    "is_lead": false
                },
            ]

        if I pass the following data:
            [
                {
                    "adviser": {"id": 2},
                    "actual_time": 220
                },
            ]

        then:
            adviser 2 gets updated
        """
        order = OrderPaidFactory(assignees=[])
        assignee1 = OrderAssigneeFactory(order=order, estimated_time=100, is_lead=True)
        assignee2 = OrderAssigneeFactory(order=order, estimated_time=250, is_lead=False)

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser': {'id': assignee2.adviser.id},
                    'actual_time': 220,
                },
            ],
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'adviser': {
                    'id': str(assignee1.adviser.id),
                    'first_name': assignee1.adviser.first_name,
                    'last_name': assignee1.adviser.last_name,
                    'name': assignee1.adviser.name,
                },
                'estimated_time': assignee1.estimated_time,
                'actual_time': None,
                'is_lead': assignee1.is_lead,
            },
            {
                'adviser': {
                    'id': str(assignee2.adviser.id),
                    'first_name': assignee2.adviser.first_name,
                    'last_name': assignee2.adviser.last_name,
                    'name': assignee2.adviser.name,
                },
                'estimated_time': assignee2.estimated_time,
                'actual_time': 220,
                'is_lead': assignee2.is_lead,
            },
        ]

    @pytest.mark.parametrize(
        'data',
        (
            {'estimated_time': 100},
            {'is_lead': True},
        ),
    )
    def test_400_if_readonly_fields_changed(self, data):
        """
        Test that estimated_time and is_lead cannot be set at this stage.
        """
        order = OrderPaidFactory(assignees=[])
        assignee = OrderAssigneeFactory(order=order)

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser': {'id': assignee.adviser.id},
                    **data,
                },
            ],
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {
                list(data)[0]: [
                    'This field cannot be changed at this stage.',
                ],
            },
        ]

    @pytest.mark.parametrize(
        'data',
        (
            {'estimated_time': 100},
            {'is_lead': True},
        ),
    )
    def test_400_if_assignee_added_with_extra_field(self, data):
        """
        Test that estimated_time and is_lead cannot be set at this stage
        even when adding a new assignee.
        """
        order = OrderPaidFactory()
        new_adviser = AdviserFactory()

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser': {
                        'id': new_adviser.id,
                    },
                    **data,
                },
            ],
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {
                list(data)[0]: [
                    'This field cannot be changed at this stage.',
                ],
            },
        ]


class TestChangeAssigneesWhenOrderInOtherAllowedStatuses(APITestMixin):
    """
    Tests related to changing order assignees when order is in
    quote_awaiting_acceptance or quote_accepted.

    - assignees can be added
    - assignees cannot be removed
    - `estimated_time`, `actual_time` and `is_lead` cannot be changed
    """

    @pytest.mark.parametrize(
        'order_status', (
            OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
            OrderStatus.QUOTE_ACCEPTED,
        ),
    )
    def test_ok_if_assignee_added(self, order_status):
        """
        Test that an assignee can be added.
        Given an order with the following assignees:
            [
                {
                    "adviser": {"id": 1},
                    "estimated_time": 100,
                    "is_lead": true
                },
                {
                    "adviser": {"id": 2},
                    "estimated_time": 250,
                    "is_lead": false
                },
            ]

        if I pass the following data:
            [
                {
                    "adviser": {"id": 3},
                },
            ]

        then:
            the adviser is added
        """
        order = OrderFactory(status=order_status)
        new_adviser = AdviserFactory()

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser': {'id': new_adviser.id},
                },
            ],
        )

        assert response.status_code == status.HTTP_200_OK
        assert str(new_adviser.id) in [item['adviser']['id'] for item in response.json()]

    @pytest.mark.parametrize(
        'order_status', (
            OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
            OrderStatus.QUOTE_ACCEPTED,
        ),
    )
    def test_400_if_assignee_deleted(self, order_status):
        """
        Test that assignees cannot be deleted.
        Given an order with the following assignees:
            [
                {
                    "adviser": {"id": 1},
                    "estimated_time": 100,
                    "is_lead": true
                },
                {
                    "adviser": {"id": 2},
                    "estimated_time": 250,
                    "is_lead": false
                },
            ]

        if I pass the following data with force_delete == True
            [
                {
                    "adviser": {"id": 1},
                },
            ]

        then:
            the response returns a validation error as no assignee can be deleted.
        """
        order = OrderFactory(status=order_status, assignees=[])
        assignee = OrderAssigneeFactory(order=order)

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            f'{url}?{AssigneeView.FORCE_DELETE_PARAM}=1',
            [
                {
                    'adviser': {'id': assignee.adviser.id},
                },
            ],
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'non_field_errors': [
                'You cannot delete any assignees at this stage.',
            ],
        }

    @pytest.mark.parametrize(
        'order_status', (
            OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
            OrderStatus.QUOTE_ACCEPTED,
        ),
    )
    @pytest.mark.parametrize(
        'data', (
            {'estimated_time': 100},
            {'actual_time': 100},
            {'is_lead': True},
        ),
    )
    def test_400_if_readonly_fields_changed(self, order_status, data):
        """
        Test that estimated_time, actual_time and is_lead cannot be set
        at this stage.
        """
        order = OrderFactory(status=order_status, assignees=[])
        assignee = OrderAssigneeFactory(order=order)

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser': {'id': assignee.adviser.id},
                    **data,
                },
            ],
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {
                list(data)[0]: [
                    'This field cannot be changed at this stage.',
                ],
            },
        ]

    @pytest.mark.parametrize(
        'order_status', (
            OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
            OrderStatus.QUOTE_ACCEPTED,
        ),
    )
    @pytest.mark.parametrize(
        'data', (
            {'estimated_time': 100},
            {'actual_time': 100},
            {'is_lead': True},
        ),
    )
    def test_400_if_assignee_added_with_extra_field(self, order_status, data):
        """
        Test that estimated_time, actual_time and is_lead cannot be set
        at this stage even when adding a new adviser.
        """
        order = OrderFactory(status=order_status)
        new_adviser = AdviserFactory()

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser': {'id': new_adviser.id},
                    **data,
                },
            ],
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {
                list(data)[0]: [
                    'This field cannot be changed at this stage.',
                ],
            },
        ]
