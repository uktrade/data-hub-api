from unittest import mock

from django.conf import settings
from django.urls import reverse
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status

from datahub.company.models import Interaction
from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase
from datahub.es.utils import document_exists, get_elasticsearch_client
from .factories import AdvisorFactory, CompanyFactory, ContactFactory, InteractionFactory


class InteractionTestCase(LeelooTestCase):
    """Interaction test case."""

    def test_interaction_detail_view(self):
        """Interaction detail view."""
        interaction = InteractionFactory()
        url = reverse('interaction-detail', kwargs={'pk': interaction.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(interaction.pk)

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_interaction(self, mocked_save_to_korben):
        """Test add new interaction."""
        url = reverse('interaction-list')
        response = self.api_client.post(url, {
            'interaction_type':
            constants.InteractionType.business_card.value.id,
            'subject': 'whatever',
            'date_of_interaction': now().isoformat(),
            'dit_advisor': AdvisorFactory().pk,
            'notes': 'hello',
            'company': CompanyFactory().pk,
            'contact': ContactFactory().pk,
            'service': constants.Service.trade_enquiry.value.id,
            'dit_team': constants.Team.healthcare_uk.value.id
        })

        assert response.status_code == status.HTTP_201_CREATED
        # make sure we're spawning a task to save to Korben
        expected_data = Interaction.objects.get(
            pk=response.data['id']).convert_model_to_korben_format()
        mocked_save_to_korben.delay.assert_called_once_with(
            db_table='company_interaction',
            data=expected_data,
            update=False,
            user_id=self.user.id)
        # make sure we're writing to ES
        es_client = get_elasticsearch_client()
        assert document_exists(
            client=es_client,
            doc_type='company_interaction',
            document_id=response.data['id'])

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    @freeze_time('2017-01-27 12:00:01')
    def test_modify_interaction(self, mocked_save_to_korben):
        """Modify an existing interaction."""
        interaction = InteractionFactory(subject='I am a subject')

        url = reverse('interaction-detail', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, {
            'subject': 'I am another subject',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'I am another subject'
        # make sure we're spawning a task to save to Korben
        expected_data = interaction.convert_model_to_korben_format()
        expected_data['subject'] = 'I am another subject'
        mocked_save_to_korben.delay.assert_called_once_with(
            db_table='company_interaction',
            data=expected_data,
            update=True,  # this is an update!
            user_id=self.user.id)
        # make sure we're writing to ES
        es_client = get_elasticsearch_client()
        es_result = es_client.get(
            index=settings.ES_INDEX,
            doc_type='company_interaction',
            id=response.data['id'],
            realtime=True)
        assert es_result['_source']['subject'] == 'I am another subject'

    def test_archive_interaction_no_reason(self):
        """Test archive interaction without providing a reason."""
        interaction = InteractionFactory()
        url = reverse('interaction-archive', kwargs={'pk': interaction.pk})
        response = self.api_client.post(url)

        assert response.data['archived']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == str(interaction.pk)

        # make sure we're writing to ES
        es_client = get_elasticsearch_client()
        es_result = es_client.get(
            index=settings.ES_INDEX,
            doc_type='company_interaction',
            id=response.data['id'],
            realtime=True)
        assert es_result['_source']['archived']
        assert es_result['_source']['archived_reason'] == ''

    def test_archive_interaction_reason(self):
        """Test archive interaction providing a reason."""
        interaction = InteractionFactory()
        url = reverse('interaction-archive', kwargs={'pk': interaction.pk})
        response = self.api_client.post(url, {'reason': 'foo'})

        assert response.data['archived']
        assert response.data['archived_reason'] == 'foo'
        assert response.data['id'] == str(interaction.pk)

        # make sure we're writing to ES
        es_client = get_elasticsearch_client()
        es_result = es_client.get(
            index=settings.ES_INDEX,
            doc_type='company_interaction',
            id=response.data['id'],
            realtime=True)
        assert es_result['_source']['archived']
        assert es_result['_source']['archived_reason'] == 'foo'

    def test_unarchive_interaction(self):
        """Test unarchive interaction."""
        interaction = InteractionFactory(archived=True, archived_reason='foo')
        url = reverse('interaction-unarchive', kwargs={'pk': interaction.pk})
        response = self.api_client.get(url)

        assert not response.data['archived']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == str(interaction.pk)
