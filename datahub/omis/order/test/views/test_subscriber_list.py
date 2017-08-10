import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import APITestMixin

from ..factories import OrderFactory, OrderSubscriberFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestGetSubscriberList(APITestMixin):
    """Get subscriber list test case."""

    def test_empty(self):
        """
        Test that calling GET returns [] if no-one is subscribed.
        """
        order = OrderFactory()

        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id}
        )
        response = self.api_client.get(url, format='json')

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
            kwargs={'order_pk': order.id}
        )
        response = self.api_client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'id': str(adviser.id),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'dit_team': {
                    'id': str(adviser.dit_team.id),
                    'name': adviser.dit_team.name
                }
            }
            for adviser in advisers[:2]
        ]

    def test_invalid_order(self):
        """Test that calling GET on an invalid order returns 404."""
        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': '00000000-0000-0000-0000-000000000000'}
        )
        response = self.api_client.get(url, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestChangeSubscriberList(APITestMixin):
    """Change subscriber list test case."""

    def test_add_to_empty_list(self):
        """
        Test that calling PUT with new advisers adds them to the subscriber list.
        """
        advisers = AdviserFactory.create_batch(2)
        order = OrderFactory()

        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id}
        )

        response = self.api_client.put(
            url,
            [{'id': adviser.id} for adviser in advisers],
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert {adv['id'] for adv in response.json()} == {str(adv.id) for adv in advisers}

    def test_change_existing_list(self):
        """
        Test that calling PUT with a different list of advisers completely changes
        the subscriber list:
        - advisers not in the list will be removed
        - new advisers will be added
        - existing advisers will be kept
        """
        previous_advisers = AdviserFactory.create_batch(2)
        order = OrderFactory()
        subscriptions = [
            OrderSubscriberFactory(order=order, adviser=adviser)
            for adviser in previous_advisers
        ]

        final_advisers = [
            AdviserFactory(),  # new
            previous_advisers[1]  # existing
        ]

        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id}
        )
        response = self.api_client.put(
            url,
            [{'id': adviser.id} for adviser in final_advisers],
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert {adv['id'] for adv in response.json()} == {str(adv.id) for adv in final_advisers}

        # check that the id of the existing subscription didn't change
        assert order.subscribers.filter(id=subscriptions[1].id).exists()

    def test_remove_all(self):
        """
        Test that calling PUT with an empty list, removes all the subscribers.
        """
        advisers = AdviserFactory.create_batch(2)
        order = OrderFactory()
        for adviser in advisers:
            OrderSubscriberFactory(order=order, adviser=adviser)

        url = reverse(
            'api-v3:omis:order:subscriber-list',
            kwargs={'order_pk': order.id}
        )
        response = self.api_client.put(url, [], format='json')

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
            kwargs={'order_pk': order.id}
        )

        data = [{'id': adviser.id} for adviser in advisers]
        data.append({
            'id': '00000000-0000-0000-0000-000000000000'
        })

        response = self.api_client.put(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == [
            {}, {}, {'id': ['00000000-0000-0000-0000-000000000000 is not a valid adviser']},
        ]
