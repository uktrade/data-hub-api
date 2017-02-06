from unittest import mock

from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdvisorFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase
from datahub.interaction.models import ServiceDelivery
from datahub.interaction.test.factories import ServiceDeliveryFactory


class ServiceDeliveryTestCase(LeelooTestCase):
    """Service Delivery test case."""

    def test_service_delivery_detail_view(self):
        """Service Delivery detail view."""
        servicedelivery = ServiceDeliveryFactory()
        url = reverse('v2:servicedelivery-detail', kwargs={'pk': servicedelivery.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(servicedelivery.pk)

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_servicedelivery(self, mocked_save_to_korben):
        """Test add new service delivery."""
        url = reverse('v2:servicedelivery-list')
        response = self.api_client.post(url, {
            'subject': 'whatever',
            'date': now().isoformat(),
            'dit_advisor': AdvisorFactory().pk,
            'notes': 'hello',
            'company': CompanyFactory().pk,
            'contact': ContactFactory().pk,
            'service': constants.Service.trade_enquiry.value.id,
            'dit_team': constants.Team.healthcare_uk.value.id
        })

        assert response.status_code == status.HTTP_201_CREATED
        # make sure we're spawning a task to save to Korben
        expected_data = ServiceDelivery.objects.get(pk=response.data['id']).convert_model_to_korben_format()
        mocked_save_to_korben.delay.assert_called_once_with(
            db_table='interaction_servicedelivery',
            data=expected_data,
            update=False,
            user_id=self.user.id
        )

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    @freeze_time('2017-01-27 12:00:01')
    def test_modify_service_delivery(self, mocked_save_to_korben):
        """Modify an existing service delivery."""
        servicedelivery = ServiceDeliveryFactory(subject='I am a subject')

        url = reverse('v2:servicedelivery-detail', kwargs={'pk': servicedelivery.pk})
        response = self.api_client.patch(url, {
            'subject': 'I am another subject',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'I am another subject'
        # make sure we're spawning a task to save to Korben
        expected_data = servicedelivery.convert_model_to_korben_format()
        expected_data['subject'] = 'I am another subject'
        mocked_save_to_korben.delay.assert_called_once_with(
            db_table='interaction_servicedelivery',
            data=expected_data,
            update=True,
            user_id=self.user.id
        )
