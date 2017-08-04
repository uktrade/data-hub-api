import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import APITestMixin

from ..factories import OrderAssigneeFactory, OrderFactory
from ...models import OrderAssignee
from ...views import AssigneeView

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestGetOrderAssignees(APITestMixin):
    """Tests related to getting the list of advisers assigned to an order."""

    def test_empty(self):
        """Test that calling GET returns [] if no-one is assigned."""
        order = OrderFactory()

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id}
        )
        response = self.api_client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_non_empty(self):
        """
        Test that calling GET returns the list of advisers assigned to the order.
        """
        advisers = AdviserFactory.create_batch(3)
        order = OrderFactory()
        for i, adviser in enumerate(advisers[:2]):
            OrderAssigneeFactory(
                order=order,
                adviser=adviser,
                estimated_time=(120 * i)
            )

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id}
        )
        response = self.api_client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'adviser_id': adviser.id,
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'estimated_time': (120 * i),
                'is_lead': False
            }
            for i, adviser in enumerate(advisers[:2])
        ]


class TestChangeOrderAssignees(APITestMixin):
    """Tests related to changing who is assigned to an order."""

    def test_add_change(self):
        """
        Tests that:
        Given an order with the following assignees:
            [
                {
                    "adviser_id": 1,
                    "first_name": "Joe",
                    "last_name": "Doe",
                    "estimated_time": 100,
                    "is_lead": true
                },
                {
                    "adviser_id": 2,
                    "first_name": "Rebecca",
                    "last_name": "Bah",
                    "estimated_time": 250,
                    "is_lead": false
                },
            ]

        if I pass the following data:
            [
                {
                    "adviser_id": 1,
                    "estimated_time": 200,
                    "is_lead": false
                },
                {
                    "adviser_id": 3,
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
        order = OrderFactory()
        adviser1 = AdviserFactory()
        adviser2 = AdviserFactory()
        adviser3 = AdviserFactory()

        assignee1 = OrderAssigneeFactory(
            order=order, adviser=adviser1, estimated_time=100, is_lead=True,
            created_by=created_by, modified_by=created_by
        )
        assignee2 = OrderAssigneeFactory(
            order=order, adviser=adviser2, estimated_time=250, is_lead=False,
            created_by=created_by, modified_by=created_by
        )

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id}
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser_id': adviser1.id,
                    'estimated_time': 200,
                    'is_lead': False
                },
                {
                    'adviser_id': adviser3.id,
                    'estimated_time': 250,
                    'is_lead': True
                }
            ],
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'adviser_id': adviser1.id,
                'first_name': adviser1.first_name,
                'last_name': adviser1.last_name,
                'estimated_time': 200,
                'is_lead': False
            },
            {
                'adviser_id': adviser2.id,
                'first_name': adviser2.first_name,
                'last_name': adviser2.last_name,
                'estimated_time': assignee2.estimated_time,
                'is_lead': False
            },
            {
                'adviser_id': adviser3.id,
                'first_name': adviser3.first_name,
                'last_name': adviser3.last_name,
                'estimated_time': 250,
                'is_lead': True
            },
        ]

        # check created_by / modified_by
        created_by.refresh_from_db()
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

    def test_remove(self):
        """
        Tests that:
        Given an order with the following assignees:
            [
                {
                    "adviser_id": 1,
                    "first_name": "Joe",
                    "last_name": "Doe",
                    "estimated_time": 100,
                    "is_lead": true
                },
                {
                    "adviser_id": 2,
                    "first_name": "Rebecca",
                    "last_name": "Bah",
                    "estimated_time": 250,
                    "is_lead": false
                },
            ]

        if I pass the following data:
            [
                {
                    "adviser_id": 1,
                    "estimated_time": 200
                },
                {
                    "adviser_id": 3,
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
            kwargs={'order_pk': order.id}
        )
        response = self.api_client.patch(
            f'{url}?{AssigneeView.FORCE_DELETE_PARAM}=1',
            [
                {
                    'adviser_id': adviser1.id,
                    'estimated_time': 200
                },
                {
                    'adviser_id': adviser3.id,
                    'estimated_time': 250
                }
            ],
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        returned_advisers = {item['adviser_id'] for item in response.json()}
        assert returned_advisers == {str(adviser1.id), str(adviser3.id)}

    def test_without_changing_any_values(self):
        """
        Tests that if I patch an assignee without changing any values,
        the db record doesn't get changed (and therefore modified_by stays the same).
        Given an order with the following assignees:
            [
                {
                    "adviser_id": 1,
                    "first_name": "Joe",
                    "last_name": "Doe",
                    "estimated_time": 100,
                    "is_lead": true
                },
                {
                    "adviser_id": 2,
                    "first_name": "Rebecca",
                    "last_name": "Bah",
                    "estimated_time": 250,
                    "is_lead": false
                },
            ]

        if I pass the following data:
            [
                {
                    "adviser_id": 1,
                    "first_name": "Joe",
                    "last_name": "Doe",
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
            created_by=created_by, modified_by=created_by
        )
        OrderAssigneeFactory(order=order, adviser=adviser2)

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id}
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser_id': adviser1.id,
                    'estimated_time': assignee1.estimated_time,
                    'is_lead': assignee1.is_lead
                }
            ],
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        created_by.refresh_from_db()
        assignee1.refresh_from_db()

        assert assignee1.created_by == created_by
        assert assignee1.modified_by == created_by

    def test_validation_error_doesnt_commit_changes(self):
        """
        Tests that:
        Given an order with the following assignees:
            [
                {
                    "adviser_id": 1,
                    "first_name": "Joe",
                    "last_name": "Doe",
                    "estimated_time": 100,
                    "is_lead": true
                },
                {
                    "adviser_id": 2,
                    "first_name": "Rebecca",
                    "last_name": "Bah",
                    "estimated_time": 250,
                    "is_lead": false
                },
            ]

        if I pass the following data:
            [
                {
                    "adviser_id": 1,
                    "estimated_time": 200
                },
                {
                    "adviser_id": 3,
                    "estimated_time": 250
                },
                {
                    "adviser_id": non-existent,
                    "estimated_time": 250
                },
            ]

        then:
            1. the response returns a validation error as the new adviser doesn't exist
            2. adviser 1 doesn't get updated
            3. adviser 3 doesn't get added
        """
        order = OrderFactory()
        adviser1 = AdviserFactory()
        adviser2 = AdviserFactory()
        adviser3 = AdviserFactory()

        OrderAssigneeFactory(order=order, adviser=adviser1, estimated_time=100, is_lead=True)
        OrderAssigneeFactory(order=order, adviser=adviser2, estimated_time=250, is_lead=False)

        url = reverse(
            'api-v3:omis:order:assignee',
            kwargs={'order_pk': order.id}
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser_id': adviser1.id,
                    'estimated_time': 200,
                    'is_lead': False
                },
                {
                    'adviser_id': adviser3.id,
                    'estimated_time': 250,
                    'is_lead': True
                },
                {
                    'adviser_id': '00000000-0000-0000-0000-000000000000',
                    'estimated_time': 300
                },
            ],
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response.json() == [
            {},
            {},
            {'adviser_id': ['00000000-0000-0000-0000-000000000000 is not a valid adviser']}
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

    def test_only_one_lead_allowed(self):
        """
        Tests that only one lead is allowed and you have to set the old lead to False
        if you want to promote a different adviser.

        Given an order with the following assignees:
            [
                {
                    "adviser_id": 1,
                    ...
                    "is_lead": true
                },
                {
                    "adviser_id": 2,
                    ...
                    "is_lead": false
                },
                {
                    "adviser_id": 3,
                    ...
                    "is_lead": false
                },
            ]

        if I pass the following data:
            [
                {
                    "adviser_id": 2,
                    "is_lead": true
                },
                {
                    "adviser_id": 3,
                    "estimated_time": 0
                },
                {
                    "adviser_id": 4,
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
            kwargs={'order_pk': order.id}
        )
        response = self.api_client.patch(
            url,
            [
                {
                    'adviser_id': adviser2.id,
                    'is_lead': True
                },
                {
                    'adviser_id': adviser3.id,
                    'estimated_time': 0
                },
                {
                    'adviser_id': adviser4.id,
                    'estimated_time': 0
                },
            ],
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'non_field_errors': ['Only one lead allowed.']}
