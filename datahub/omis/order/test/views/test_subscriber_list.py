import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.test.factories import OrderFactory, OrderSubscriberFactory


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestGetSubscriberList(APITestMixin):
    """Get subscriber list test case."""

    def test_access_is_denied_if_without_permissions(self):
        """Test that a 403 is returned if the user has no permissions."""
        order = OrderFactory()
        user = create_test_user()
        api_client = self.create_api_client(user=user)
        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id},
        )

        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_access_allowed_if_with_view_permission(self):
        """Test that a 200 is returned if the user has the view permission."""
        order = OrderFactory()
        user = create_test_user(permission_codenames=['view_ordersubscriber'])
        api_client = self.create_api_client(user=user)
        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id},
        )

        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_empty(self):
        """
        Test that calling GET returns [] if no-one is subscribed.
        """
        order = OrderFactory()

        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_non_empty(self):
        """
        Test that calling GET returns the list of advisers subscribed to the order.
        """
        advisers = AdviserFactory.create_batch(3)
        order = OrderFactory()
        for adviser in advisers[:2]:
            OrderSubscriberFactory(order=order, adviser=adviser)

        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'id': str(adviser.id),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
                'dit_team': {
                    'id': str(adviser.dit_team.id),
                    'name': adviser.dit_team.name,
                    'uk_region': {
                        'id': str(adviser.dit_team.uk_region.pk),
                        'name': adviser.dit_team.uk_region.name,
                    },
                },
            }
            for adviser in advisers[:2]
        ]

    def test_invalid_order(self):
        """Test that calling GET on an invalid order returns 404."""
        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': '00000000-0000-0000-0000-000000000000'},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestChangeSubscriberList(APITestMixin):
    """Change subscriber list test case."""

    def test_access_is_denied_if_without_permissions(self):
        """Test that a 403 is returned if the user has no permissions."""
        order = OrderFactory()

        user = create_test_user()
        api_client = self.create_api_client(user=user)
        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id},
        )
        response = api_client.put(url, data=[])

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_access_allowed_if_with_change_permission(self):
        """Test that a 200 is returned if the user has the change permission."""
        order = OrderFactory()

        user = create_test_user(permission_codenames=['change_ordersubscriber'])
        api_client = self.create_api_client(user=user)
        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id},
        )
        response = api_client.put(url, data=[])

        assert response.status_code == status.HTTP_200_OK

    def test_add_to_empty_list(self):
        """
        Test that calling PUT with new advisers adds them to the subscriber list.
        """
        advisers = AdviserFactory.create_batch(2)
        order = OrderFactory()

        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id},
        )

        response = self.api_client.put(
            url,
            [{'id': adviser.id} for adviser in advisers],
        )

        assert response.status_code == status.HTTP_200_OK
        assert {adv['id'] for adv in response.json()} == {str(adv.id) for adv in advisers}

    @pytest.mark.parametrize(
        'allowed_status', (
            OrderStatus.DRAFT,
            OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
            OrderStatus.QUOTE_ACCEPTED,
            OrderStatus.PAID,
        ),
    )
    def test_change_existing_list(self, allowed_status):
        """
        Test that calling PUT with a different list of advisers completely changes
        the subscriber list:
        - advisers not in the list will be removed
        - new advisers will be added
        - existing advisers will be kept
        """
        previous_advisers = AdviserFactory.create_batch(2)
        order = OrderFactory(status=allowed_status)
        subscriptions = [
            OrderSubscriberFactory(order=order, adviser=adviser)
            for adviser in previous_advisers
        ]

        final_advisers = [
            AdviserFactory(),  # new
            previous_advisers[1],  # existing
        ]

        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.put(
            url,
            [{'id': adviser.id} for adviser in final_advisers],
        )

        assert response.status_code == status.HTTP_200_OK
        assert {adv['id'] for adv in response.json()} == {str(adv.id) for adv in final_advisers}

        # check that the id of the existing subscription didn't change
        assert order.subscribers.filter(id=subscriptions[1].id).exists()

    @pytest.mark.parametrize(
        'allowed_status', (
            OrderStatus.DRAFT,
            OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
            OrderStatus.QUOTE_ACCEPTED,
            OrderStatus.PAID,
        ),
    )
    def test_remove_all(self, allowed_status):
        """
        Test that calling PUT with an empty list, removes all the subscribers.
        """
        advisers = AdviserFactory.create_batch(2)
        order = OrderFactory(status=allowed_status)
        for adviser in advisers:
            OrderSubscriberFactory(order=order, adviser=adviser)

        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id},
        )
        response = self.api_client.put(url, [])

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_invalid_adviser(self):
        """
        Test that calling PUT with an invalid adviser returns 400.
        """
        advisers = AdviserFactory.create_batch(2)
        order = OrderFactory()

        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id},
        )

        data = [{'id': adviser.id} for adviser in advisers]
        data.append({
            'id': '00000000-0000-0000-0000-000000000000',
        })

        response = self.api_client.put(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {}, {}, {'id': ['00000000-0000-0000-0000-000000000000 is not a valid adviser']},
        ]

    @pytest.mark.parametrize(
        'disallowed_status', (
            OrderStatus.COMPLETE,
            OrderStatus.CANCELLED,
        ),
    )
    def test_409_if_order_in_disallowed_status(self, disallowed_status):
        """
        Test that if the order is not in one of the allowed statuses, the endpoint
        returns 409.
        """
        order = OrderFactory(status=disallowed_status)

        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id},
        )

        response = self.api_client.put(
            url,
            [{'id': AdviserFactory().id}],
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {
            'detail': (
                'The action cannot be performed '
                f'in the current status {disallowed_status.label}.'
            ),
        }
