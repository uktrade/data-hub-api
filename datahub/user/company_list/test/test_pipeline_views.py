from uuid import uuid4

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import ArchivedCompanyFactory, CompanyFactory, ContactFactory
from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime
from datahub.metadata.test.factories import SectorFactory
from datahub.user.company_list.models import PipelineItem
from datahub.user.company_list.test.factories import (
    ArchivedPipelineItemFactory,
    PipelineItemFactory,
)

pipeline_collection_url = reverse('api-v4:company-list:pipelineitem-collection')


def _pipeline_item_detail_url(item_pk):
    return reverse('api-v4:company-list:pipelineitem-detail', kwargs={'pk': item_pk})


def _pipeline_item_archive_url(item_pk):
    return reverse('api-v4:company-list:pipelineitem-archive', kwargs={'pk': item_pk})


def _pipeline_item_unarchive_url(item_pk):
    return reverse('api-v4:company-list:pipelineitem-unarchive', kwargs={'pk': item_pk})


class TestGetPipelineItemsView(APITestMixin):
    """Tests for getting pipeline items."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        response = api_client.get(pipeline_collection_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['view_pipelineitem'], status.HTTP_200_OK),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status, api_client):
        """Test that the expected status is returned for various user permissions."""
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)
        PipelineItemFactory(adviser=user)

        api_client = self.create_api_client(user=user)
        response = api_client.get(pipeline_collection_url)
        assert response.status_code == expected_status

    def test_returns_empty_list_if_pipeline_doesnt_exist(self):
        """Test that an empty list is returned if the there are no pipeline items."""
        response = self.api_client.get(pipeline_collection_url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['results']) == 0

    def test_can_retrieve_a_single_pipeline_item(self):
        """Test that details of a single pipeline item can be retrieved."""
        company = CompanyFactory()
        item = PipelineItemFactory(adviser=self.user, company=company)
        response = self.api_client.get(pipeline_collection_url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 1

        self._assert_get_pipeline_items_response(
            response_data['results'][0],
            company,
            item,
        )

    @pytest.fixture
    def items(self):
        """Set up items test fixtures."""
        names = ('ABC', 'BCA', 'CAB')
        data = []
        with freeze_time('Jan 14th, 2020', auto_tick_seconds=15):
            for name in names:
                data.append(PipelineItemFactory(
                    adviser=self.user,
                    name=name,
                ))
            return data

    def test_default_is_sorted_by_created_on_desc(self, items):
        """Test the response is sorted by created on descending by default."""
        response = self.api_client.get(pipeline_collection_url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 3

        self._assert_get_pipeline_items_response(
            response_data['results'][0],
            items[2].company,
            items[2],
        )
        self._assert_get_pipeline_items_response(
            response_data['results'][1],
            items[1].company,
            items[1],
        )
        self._assert_get_pipeline_items_response(
            response_data['results'][2],
            items[0].company,
            items[0],
        )

    def test_can_sort_by_created_on_asc(self, items):
        """Test the response can be sorted by created on ascending."""
        response = self.api_client.get(
            pipeline_collection_url,
            data={'sortby': 'created_on'},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 3

        self._assert_get_pipeline_items_response(
            response_data['results'][0],
            items[0].company,
            items[0],
        )
        self._assert_get_pipeline_items_response(
            response_data['results'][1],
            items[1].company,
            items[1],
        )
        self._assert_get_pipeline_items_response(
            response_data['results'][2],
            items[2].company,
            items[2],
        )

    def test_can_sort_by_modified_on_desc(self, items):
        """Test the response can be sorted by modified on descending."""
        item = items[1]
        item.name = 'modified'
        item.save()
        response = self.api_client.get(
            pipeline_collection_url,
            data={'sortby': '-modified_on'},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 3

        self._assert_get_pipeline_items_response(
            response_data['results'][0],
            items[1].company,
            items[1],
        )
        self._assert_get_pipeline_items_response(
            response_data['results'][1],
            items[2].company,
            items[2],
        )
        self._assert_get_pipeline_items_response(
            response_data['results'][2],
            items[0].company,
            items[0],
        )

    def test_can_sort_by_modified_on_ascending(self, items):
        """Test the response can be sorted by modified on ascending."""
        item = items[1]
        item.name = 'modified'
        item.save()
        response = self.api_client.get(
            pipeline_collection_url,
            data={'sortby': 'modified_on'},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 3

        self._assert_get_pipeline_items_response(
            response_data['results'][0],
            items[0].company,
            items[0],
        )
        self._assert_get_pipeline_items_response(
            response_data['results'][1],
            items[2].company,
            items[2],
        )
        self._assert_get_pipeline_items_response(
            response_data['results'][2],
            items[1].company,
            items[1],
        )

    def test_can_sort_by_name_descending(self, items):
        """Test the response can be sorted by name decending."""
        response = self.api_client.get(
            pipeline_collection_url,
            data={'sortby': 'name'},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 3

        self._assert_get_pipeline_items_response(
            response_data['results'][0],
            items[0].company,
            items[0],
        )
        self._assert_get_pipeline_items_response(
            response_data['results'][1],
            items[1].company,
            items[1],
        )
        self._assert_get_pipeline_items_response(
            response_data['results'][2],
            items[2].company,
            items[2],
        )

    def test_can_sort_by_name_ascending(self, items):
        """Test the response can be sorted by name ascending."""
        response = self.api_client.get(
            pipeline_collection_url,
            data={'sortby': '-name'},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 3

        self._assert_get_pipeline_items_response(
            response_data['results'][0],
            items[2].company,
            items[2],
        )
        self._assert_get_pipeline_items_response(
            response_data['results'][1],
            items[1].company,
            items[1],
        )
        self._assert_get_pipeline_items_response(
            response_data['results'][2],
            items[0].company,
            items[0],
        )

    @pytest.mark.parametrize(
        'request_data,count',
        (
            pytest.param(
                {'status': PipelineItem.Status.IN_PROGRESS},
                1,
                id='valid status',
            ),
            pytest.param(
                {'status': PipelineItem.Status.LEADS},
                0,
                id='non existent status',
            ),
        ),
    )
    def test_can_filter_by_valid_status(self, request_data, count):
        """Test that it can filter by status."""
        PipelineItemFactory(
            adviser=self.user,
            company=CompanyFactory(),
            status=PipelineItem.Status.WIN,
        )
        PipelineItemFactory(
            adviser=self.user,
            company=CompanyFactory(),
            status=PipelineItem.Status.IN_PROGRESS,
        )

        response = self.api_client.get(
            pipeline_collection_url,
            data=request_data,
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == count

    def test_returns_400_when_filtering_with_invalid_status(self):
        """Test that it can filter by status."""
        PipelineItemFactory(
            adviser=self.user,
            company=CompanyFactory(),
            status=PipelineItem.Status.WIN,
        )

        response = self.api_client.get(
            pipeline_collection_url,
            data={'status': 'invalid'},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'status': ['Select a valid choice. invalid is not one of the available choices.'],
        }

    def test_can_filter_by_company(self):
        """Test that it can filter by company."""
        company_1 = CompanyFactory()
        PipelineItemFactory(
            adviser=self.user,
            company=company_1,
            status=PipelineItem.Status.WIN,
        )
        company_2 = CompanyFactory()
        PipelineItemFactory(
            adviser=self.user,
            company=company_2,
            status=PipelineItem.Status.IN_PROGRESS,
        )

        response = self.api_client.get(
            pipeline_collection_url,
            data={'company_id': company_1.id},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 1

    def test_can_filter_by_non_existent_company(self):
        """Test that it can filter by company that is not in pipeline items."""
        company_1 = CompanyFactory()
        PipelineItemFactory(
            adviser=self.user,
            company=company_1,
            status=PipelineItem.Status.WIN,
        )
        company_2 = CompanyFactory()
        PipelineItemFactory(
            adviser=self.user,
            company=company_2,
            status=PipelineItem.Status.IN_PROGRESS,
        )

        company_3 = CompanyFactory()
        response = self.api_client.get(
            pipeline_collection_url,
            data={'company_id': company_3.id},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 0

    def test_can_filter_by_company_and_status(self):
        """Test that it can filter by company and status works."""
        company_1 = CompanyFactory()
        PipelineItemFactory(
            adviser=self.user,
            company=company_1,
            status=PipelineItem.Status.WIN,
        )
        company_2 = CompanyFactory()
        PipelineItemFactory(
            adviser=self.user,
            company=company_2,
            status=PipelineItem.Status.IN_PROGRESS,
        )

        response = self.api_client.get(
            pipeline_collection_url,
            data={
                'status': PipelineItem.Status.WIN,
                'company_id': company_1.id,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 1

    def test_returns_400_when_filtering_with_invalid_company(self):
        """Test that it can filter by company that doesn't exist gives an error."""
        company_1 = CompanyFactory()
        PipelineItemFactory(
            adviser=self.user,
            company=company_1,
            status=PipelineItem.Status.WIN,
        )
        company_2 = CompanyFactory()
        PipelineItemFactory(
            adviser=self.user,
            company=company_2,
            status=PipelineItem.Status.IN_PROGRESS,
        )

        response = self.api_client.get(
            pipeline_collection_url,
            data={'company_id': str(uuid4())},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_empty_list_when_specific_user_has_no_pipeline_items(self):
        """Test that another user's pipeline item can't be retrieved."""
        PipelineItemFactory()
        response = self.api_client.get(pipeline_collection_url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['results']) == 0

    def test_returns_only_users_pipeline_items(self):
        """Test that only the users pipeline items can be retrieved."""
        company = CompanyFactory()
        PipelineItemFactory(company=company, status=PipelineItem.Status.IN_PROGRESS)
        PipelineItemFactory(adviser=self.user, company=company, status=PipelineItem.Status.WIN)
        response = self.api_client.get(pipeline_collection_url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 1
        assert response_data['results'][0]['status'] == PipelineItem.Status.WIN

    def _assert_get_pipeline_items_response(self, response_data, company, item):
        assert response_data == {
            'company': {
                'id': str(company.pk),
                'name': company.name,
                'turnover': company.turnover,
                'export_potential': company.export_potential,
            },
            'id': str(item.id),
            'name': item.name,
            'status': item.status,
            'created_on': format_date_or_datetime(item.created_on),
            'modified_on': format_date_or_datetime(item.modified_on),
            'contact': {
                'id': str(item.contact.pk),
                'name': item.contact.name,
            },
            'sector': {
                'id': str(item.sector.pk),
                'segment': item.sector.segment,
            },
            'potential_value': str(item.potential_value),
            'likelihood_to_win': item.likelihood_to_win,
            'expected_win_date': format_date_or_datetime(item.expected_win_date),
            'archived': item.archived,
            'archived_on': None,
            'archived_reason': None,
        }

    def test_can_filter_by_archived(self):
        """Test that it can filter by archived."""
        PipelineItemFactory(
            adviser=self.user,
            status=PipelineItem.Status.WIN,
            archived=True,
        )

        PipelineItemFactory(
            adviser=self.user,
            status=PipelineItem.Status.IN_PROGRESS,
        )

        response = self.api_client.get(
            pipeline_collection_url,
            data={'archived': True},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 1
        assert response_data['results'][0]['archived'] is True

    def test_can_filter_by_not_archived(self):
        """Test that it can filter by archived."""
        PipelineItemFactory(
            adviser=self.user,
            status=PipelineItem.Status.WIN,
            archived=True,
        )

        PipelineItemFactory(
            adviser=self.user,
            status=PipelineItem.Status.IN_PROGRESS,
        )

        response = self.api_client.get(
            pipeline_collection_url,
            data={'archived': False},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 1
        assert response_data['results'][0]['archived'] is False

    def test_no_archive_filter_returns_all_results(self):
        """Test archived and non archived are returned when archive filter is not present."""
        PipelineItemFactory(
            adviser=self.user,
            status=PipelineItem.Status.WIN,
            archived=True,
        )

        PipelineItemFactory(
            adviser=self.user,
            status=PipelineItem.Status.IN_PROGRESS,
        )

        response = self.api_client.get(
            pipeline_collection_url,
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 2
        assert response_data['results'][0]['archived'] is False
        assert response_data['results'][1]['archived'] is True


class TestAddPipelineItemView(APITestMixin):
    """Tests for adding a pipeline item."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        response = api_client.post(pipeline_collection_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['view_pipelineitem'], status.HTTP_403_FORBIDDEN),
            (['add_pipelineitem'], status.HTTP_201_CREATED),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status):
        """Test that the expected status is returned for various user permissions."""
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)

        api_client = self.create_api_client(user=user)
        company = CompanyFactory()
        pipeline_status = PipelineItem.Status.LEADS
        response = api_client.post(
            pipeline_collection_url,
            data={
                'company': str(company.pk),
                'name': 'project name',
                'status': pipeline_status,
            },
        )
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        'request_data,expected_errors',
        (
            pytest.param(
                {},
                {
                    'company': ['This field is required.'],
                    'status': ['This field is required.'],
                },
                id='company and status are omitted',
            ),
            pytest.param(
                {
                    'company': None,
                },
                {
                    'company': ['This field may not be null.'],
                    'status': ['This field is required.'],
                },
                id='company is null and status is omitted',
            ),
            pytest.param(
                {
                    'status': None,
                },
                {
                    'company': ['This field is required.'],
                    'status': ['This field may not be null.'],
                },
                id='company is omitted and status is null',
            ),
            pytest.param(
                {
                    'name': None,
                },
                {
                    'company': ['This field is required.'],
                    'status': ['This field is required.'],
                    'name': ['This field may not be null.'],
                },
                id='company and status are omitted and name is null',
            ),
            pytest.param(
                {
                    'company': '',
                    'status': '',
                    'name': '',
                },
                {
                    'company': ['This field may not be null.'],
                    'status': ['"" is not a valid choice.'],
                    'name': ['This field may not be blank.'],
                },
                id='company, status and name are empty strings',
            ),
            pytest.param(
                {
                    'company': '',
                    'status': PipelineItem.Status.LEADS,
                    'name': 'project name',
                },
                {
                    'company': ['This field may not be null.'],
                },
                id='company is empty string',
            ),
        ),
    )
    def test_validation(self, request_data, expected_errors):
        """Test validation."""
        response = self.api_client.post(
            pipeline_collection_url,
            data=request_data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_errors

    def test_validate_name(self):
        """Test that a pipeline item cannot be created without name."""
        company = CompanyFactory()

        pipeline_status = PipelineItem.Status.LEADS
        response = self.api_client.post(
            pipeline_collection_url,
            data={
                'company': str(company.pk),
                'status': pipeline_status,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'non_field_errors': ['This field is required.'],
        }

    def test_validate_non_existent_contact(self):
        """Test that non existent contact adding results in error"""
        company = CompanyFactory()
        dummy_contact_id = str(uuid4())
        pipeline_status = PipelineItem.Status.LEADS
        response = self.api_client.post(
            pipeline_collection_url,
            data={
                'company': str(company.pk),
                'status': pipeline_status,
                'name': 'project name',
                'contact': dummy_contact_id,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'contact': [f'Invalid pk "{dummy_contact_id}" - object does not exist.'],
        }

    def test_validate_contact_belongs_to_company(self):
        """Test that contact being added belongs to company"""
        company = CompanyFactory()
        contact = ContactFactory()
        pipeline_status = PipelineItem.Status.LEADS
        response = self.api_client.post(
            pipeline_collection_url,
            data={
                'company': str(company.pk),
                'status': pipeline_status,
                'name': 'project name',
                'contact': str(contact.pk),
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'contact': ['Contact does not belong to company.'],
        }

    def test_validate_non_existent_sector(self):
        """Test that non existent sector adding results in error"""
        company = CompanyFactory()
        dummy_sector_id = str(uuid4())
        pipeline_status = PipelineItem.Status.LEADS
        response = self.api_client.post(
            pipeline_collection_url,
            data={
                'company': str(company.pk),
                'status': pipeline_status,
                'name': 'project name',
                'sector': dummy_sector_id,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'sector': [f'Invalid pk "{dummy_sector_id}" - object does not exist.'],
        }

    @freeze_time('2017-04-19 15:25:30.986208')
    def test_successfully_create_a_pipeline_item_partial_data(self):
        """Test that a pipeline item can be created with minimal data."""
        company = CompanyFactory()

        pipeline_status = PipelineItem.Status.LEADS
        response = self.api_client.post(
            pipeline_collection_url,
            data={
                'company': str(company.pk),
                'name': 'project name',
                'status': pipeline_status,
            },
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_201_CREATED

        assert response_data == {
            'id': response_data['id'],
            'name': 'project name',
            'company': {
                'id': str(company.pk),
                'name': company.name,
                'export_potential': company.export_potential,
                'turnover': company.turnover,
            },
            'status': pipeline_status,
            'created_on': '2017-04-19T15:25:30.986208Z',
            'modified_on': '2017-04-19T15:25:30.986208Z',
            'contact': None,
            'sector': None,
            'potential_value': None,
            'likelihood_to_win': None,
            'expected_win_date': None,
            'archived': False,
            'archived_on': None,
            'archived_reason': None,
        }

        pipeline_item = PipelineItem.objects.get(pk=response_data['id'])

        # adviser should be set to the authenticated user
        assert pipeline_item.adviser == self.user
        assert pipeline_item.created_by == self.user
        assert pipeline_item.modified_by == self.user

    @freeze_time('2017-04-19 15:25:30.986208')
    def test_successfully_create_a_pipeline_item_full_data(self):
        """Test that a pipeline item can be created with all fields."""
        company = CompanyFactory()
        sector = SectorFactory()
        contact = ContactFactory(company=company)

        pipeline_status = PipelineItem.Status.LEADS
        response = self.api_client.post(
            pipeline_collection_url,
            data={
                'company': str(company.pk),
                'name': 'project name',
                'status': pipeline_status,
                'contact': str(contact.pk),
                'sector': str(sector.pk),
                'likelihood_to_win': PipelineItem.LikelihoodToWin.LOW,
                'expected_win_date': '2019-04-19',
                'potential_value': 1000,
                'archived': False,
                'archived_on': None,
                'archived_reason': None,
            },
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_201_CREATED

        assert response_data == {
            'id': response_data['id'],
            'name': 'project name',
            'company': {
                'id': str(company.pk),
                'name': company.name,
                'export_potential': company.export_potential,
                'turnover': company.turnover,
            },
            'status': pipeline_status,
            'created_on': '2017-04-19T15:25:30.986208Z',
            'modified_on': '2017-04-19T15:25:30.986208Z',
            'contact': {
                'id': str(contact.pk),
                'name': contact.name,
            },
            'sector': {
                'id': str(sector.pk),
                'segment': sector.segment,
            },
            'potential_value': str(1000),
            'likelihood_to_win': PipelineItem.LikelihoodToWin.LOW,
            'expected_win_date': '2019-04-19',
            'archived': False,
            'archived_on': None,
            'archived_reason': None,
        }

        pipeline_item = PipelineItem.objects.get(pk=response_data['id'])

        # adviser should be set to the authenticated user
        assert pipeline_item.adviser == self.user
        assert pipeline_item.created_by == self.user
        assert pipeline_item.modified_by == self.user

    @freeze_time('2017-04-19 15:25:30.986208')
    def test_add_pipeline_item_with_same_company_as_existing_to_the_user(self):
        """Test that a pipeline item with same company can be added to the same user again."""
        company = CompanyFactory()
        PipelineItemFactory(company=company, adviser=self.user)

        response = self.api_client.post(
            pipeline_collection_url,
            data={
                'company': str(company.pk),
                'name': 'project name',
                'status': PipelineItem.Status.IN_PROGRESS,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'name': 'project name',
            'company': {
                'id': str(company.pk),
                'name': company.name,
                'export_potential': company.export_potential,
                'turnover': company.turnover,
            },
            'status': 'in_progress',
            'created_on': '2017-04-19T15:25:30.986208Z',
            'modified_on': '2017-04-19T15:25:30.986208Z',
            'contact': None,
            'sector': None,
            'potential_value': None,
            'likelihood_to_win': None,
            'expected_win_date': None,
            'archived': False,
            'archived_on': None,
            'archived_reason': None,
        }

    @freeze_time('2017-04-19 15:25:30.986208')
    def test_adding_existing_company_with_same_pipeline_item_name(self):
        """Test that same company can be added to the same pipeline item name."""
        company = CompanyFactory()
        PipelineItemFactory(
            company=company,
            adviser=self.user,
            name='project name',
        )

        response = self.api_client.post(
            pipeline_collection_url,
            data={
                'company': str(company.pk),
                'name': 'project name',
                'status': PipelineItem.Status.IN_PROGRESS,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'name': 'project name',
            'company': {
                'id': str(company.pk),
                'name': company.name,
                'export_potential': company.export_potential,
                'turnover': company.turnover,
            },
            'status': 'in_progress',
            'created_on': '2017-04-19T15:25:30.986208Z',
            'modified_on': '2017-04-19T15:25:30.986208Z',
            'contact': None,
            'sector': None,
            'potential_value': None,
            'likelihood_to_win': None,
            'expected_win_date': None,
            'archived': False,
            'archived_on': None,
            'archived_reason': None,
        }

    def test_with_archived_company(self):
        """Test adding an archived company."""
        company = ArchivedCompanyFactory()

        response = self.api_client.post(
            pipeline_collection_url,
            data={
                'company': str(company.pk),
                'name': 'project name',
                'status': PipelineItem.Status.IN_PROGRESS,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company': ["An archived company can't be added to the pipeline."],
        }

    def test_with_non_existent_company(self):
        """Test adding a non existent company."""
        dummy_company_id = uuid4()
        response = self.api_client.post(
            pipeline_collection_url,
            data={
                'company': dummy_company_id,
                'name': 'project name',
                'status': PipelineItem.Status.IN_PROGRESS,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company': [
                f'Invalid pk "{dummy_company_id}" - object does not exist.',
            ],
        }

    def test_same_company_can_be_added_to_different_users(self):
        """Test that same company can be added to differnt users."""
        company = CompanyFactory()
        PipelineItemFactory(company=company)

        response = self.api_client.post(
            pipeline_collection_url,
            data={
                'company': str(company.pk),
                'name': 'project name',
                'status': PipelineItem.Status.IN_PROGRESS,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_contact_copied_to_contacts(self):
        """
        Test that the value provided in the contact field is copied to contacts when a
        PipelineItem is created.
        TODO: remove once the contacts field has fully replaced the contact field.
        """
        company = CompanyFactory()
        sector = SectorFactory()
        contact = ContactFactory(company=company)

        pipeline_status = PipelineItem.Status.LEADS
        response = self.api_client.post(
            pipeline_collection_url,
            data={
                'company': str(company.pk),
                'name': 'project name',
                'status': pipeline_status,
                'contact': str(contact.pk),
                'sector': str(sector.pk),
                'likelihood_to_win': PipelineItem.LikelihoodToWin.LOW,
                'expected_win_date': '2019-04-19',
                'potential_value': 1000,
                'archived': False,
                'archived_on': None,
                'archived_reason': None,
            },
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_201_CREATED

        pipeline_item = PipelineItem.objects.get(pk=response_data['id'])
        assert pipeline_item.contact == contact
        assert list(pipeline_item.contacts.all()) == [contact]


class TestPatchPipelineItemView(APITestMixin):
    """Tests for patching a pipeline item."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        url = _pipeline_item_detail_url(uuid4())
        response = api_client.patch(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['view_pipelineitem'], status.HTTP_403_FORBIDDEN),
            (['change_pipelineitem'], status.HTTP_200_OK),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status, api_client):
        """Test that the expected status is returned for various user permissions."""
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)
        item = PipelineItemFactory(adviser=user)
        url = _pipeline_item_detail_url(item.pk)

        api_client = self.create_api_client(user=user)
        response = api_client.patch(
            url,
            data={
                'status': 'leads',
            },
        )
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        'request_data,expected_errors',
        (
            pytest.param(
                {
                    'status': None,
                },
                {
                    'status': ['This field may not be null.'],
                },
                id='status is null',
            ),
            pytest.param(
                {
                    'status': '',
                },
                {
                    'status': ['"" is not a valid choice.'],
                },
                id='status is not a valid choice',
            ),
            pytest.param(
                {
                    'status': 'invalid',
                },
                {
                    'status': ['"invalid" is not a valid choice.'],
                },
                id='status is not a valid choice',
            ),
            pytest.param(
                {
                    'company': None,
                },
                {
                    'company': ['This field may not be null.'],
                },
                id='company is not  null',
            ),
            pytest.param(
                {
                    'company': '',
                },
                {
                    'company': ['This field may not be null.'],
                },
                id='company is not a empty string',
            ),
            pytest.param(
                {
                    'name': None,
                },
                {
                    'name': ['This field may not be null.'],
                },
                id='name is not  null',
            ),
            pytest.param(
                {
                    'name': '',
                },
                {
                    'name': ['This field may not be blank.'],
                },
                id='name is not a empty string',
            ),
        ),
    )
    def test_validation(self, request_data, expected_errors):
        """Test validation."""
        item = PipelineItemFactory(adviser=self.user)
        url = _pipeline_item_detail_url(item.pk)
        response = self.api_client.patch(url, data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_errors

    def test_validate_only_allowed_fields_can_be_updated(self):
        """Test that any other field other than status or name throws a 400"""
        company = CompanyFactory()
        item = PipelineItemFactory(adviser=self.user)
        url = _pipeline_item_detail_url(item.pk)
        response = self.api_client.patch(url, data={'company': company.pk})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'company': ['field not allowed to be update.']}

    def test_patch_a_pipeline_item(self):
        """Test that status and name of a pipeline item can be patched."""
        company = CompanyFactory()
        item = PipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.WIN,
        )
        url = _pipeline_item_detail_url(item.pk)
        new_status = PipelineItem.Status.LEADS
        new_name = 'BATMAN'
        response = self.api_client.patch(
            url,
            data={
                'status': new_status,
                'name': new_name,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data == {
            'company': {
                'id': str(company.pk),
                'name': company.name,
                'turnover': company.turnover,
                'export_potential': company.export_potential,
            },
            'id': str(item.id),
            'name': new_name,
            'status': new_status,
            'created_on': format_date_or_datetime(item.created_on),
            'modified_on': format_date_or_datetime(item.modified_on),
            'contact': {
                'id': str(item.contact.pk),
                'name': item.contact.name,
            },
            'sector': {
                'id': str(item.sector.pk),
                'segment': item.sector.segment,
            },
            'potential_value': str(item.potential_value),
            'likelihood_to_win': item.likelihood_to_win,
            'expected_win_date': format_date_or_datetime(item.expected_win_date),
            'archived': False,
            'archived_on': None,
            'archived_reason': None,
        }

    @pytest.mark.parametrize(
        'field,value',
        (
            pytest.param(
                'status',
                PipelineItem.Status.LEADS,
                id='patch status',
            ),
            pytest.param(
                'name',
                'new name',
                id='patch name',
            ),
            pytest.param(
                'potential_value',
                '20000000',
                id='patch potential_value',
            ),
            pytest.param(
                'potential_value',
                None,
                id='patch potential_value_null',
            ),
            pytest.param(
                'likelihood_to_win',
                PipelineItem.LikelihoodToWin.HIGH,
                id='patch likelihood_to_win',
            ),
            pytest.param(
                'likelihood_to_win',
                None,
                id='patch likelihood_to_win_null',
            ),
            pytest.param(
                'expected_win_date',
                '2021-04-19',
                id='patch expected_win_date',
            ),
            pytest.param(
                'expected_win_date',
                None,
                id='patch expected_win_date',
            ),
        ),
    )
    def test_can_patch_an_individual_field_values(self, field, value):
        """Test that each field of a pipeline item can be patched."""
        company = CompanyFactory()
        item = PipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.WIN,
        )
        url = _pipeline_item_detail_url(item.pk)
        response = self.api_client.patch(
            url,
            data={field: value},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data[field] == value

    def test_cannot_patch_non_existent_sector(self):
        """Test that non existent sector can't be patched."""
        company = CompanyFactory()
        dummy_sector_id = str(uuid4())
        item = PipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.WIN,
        )
        url = _pipeline_item_detail_url(item.pk)
        response = self.api_client.patch(
            url,
            data={'sector': dummy_sector_id},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'sector': [f'Invalid pk "{dummy_sector_id}" - object does not exist.'],
        }

    def test_can_patch_sector_field(self):
        """Test that sector can be patched."""
        company = CompanyFactory()
        sector = SectorFactory()
        item = PipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.WIN,
        )
        url = _pipeline_item_detail_url(item.pk)
        response = self.api_client.patch(
            url,
            data={'sector': str(sector.id)},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['sector']['id'] == str(sector.id)

    def test_can_patch_sector_field_to_null(self):
        """Test that sector can be patched to null."""
        company = CompanyFactory()
        item = PipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.WIN,
        )
        url = _pipeline_item_detail_url(item.pk)
        response = self.api_client.patch(
            url,
            data={'sector': None},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['sector'] is None

    def test_can_patch_contact_field(self):
        """Test that contact can be patched."""
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        item = PipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.WIN,
        )
        url = _pipeline_item_detail_url(item.pk)
        response = self.api_client.patch(
            url,
            data={'contact': str(contact.id)},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['contact']['id'] == str(contact.id)

    def test_can_patch_contact_field_null(self):
        """Test that contact can be patched back to null."""
        company = CompanyFactory()
        item = PipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.WIN,
        )
        url = _pipeline_item_detail_url(item.pk)
        response = self.api_client.patch(
            url,
            data={'contact': None},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['contact'] is None

    def test_cannot_patch_non_existent_contact(self):
        """Test that non existent contact can't be patched."""
        company = CompanyFactory()
        dummy_contact_id = str(uuid4())
        item = PipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.WIN,
        )
        url = _pipeline_item_detail_url(item.pk)
        response = self.api_client.patch(
            url,
            data={'contact': dummy_contact_id},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'contact': [f'Invalid pk "{dummy_contact_id}" - object does not exist.'],
        }

    def test_cannot_patch_other_company_contact(self):
        """Test that contact can be patched."""
        company = CompanyFactory()
        contact = ContactFactory()
        item = PipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.WIN,
        )
        url = _pipeline_item_detail_url(item.pk)
        response = self.api_client.patch(
            url,
            data={'contact': str(contact.id)},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'contact': ['Contact does not belong to company.']}

    def test_contact_copied_to_contacts(self):
        """
        Test that the value provided in the contact field is copied to contacts when a
        pipeline item is updated.
        TODO: remove once the contacts field has fully replaced the contact field.
        """
        company = CompanyFactory()
        item = PipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.WIN,
            contacts=[],
        )
        new_contact = ContactFactory(company=company)
        url = _pipeline_item_detail_url(item.pk)
        response = self.api_client.patch(
            url,
            data={'contact': str(new_contact.id)},
        )
        assert response.status_code == status.HTTP_200_OK
        item.refresh_from_db()
        assert item.contact == new_contact
        assert list(item.contacts.all()) == [new_contact]

    def test_cannot_patch_other_users_item(self):
        """Test that cannot patch other users item."""
        item = PipelineItemFactory()
        url = _pipeline_item_detail_url(item.pk)
        response = self.api_client.patch(
            url,
            data={
                'status': PipelineItem.Status.LEADS,
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_404_no_item_to_patch(self):
        """Test that 404 is returned when no item."""
        url = _pipeline_item_detail_url(uuid4())
        response = self.api_client.patch(
            url,
            data={
                'status': PipelineItem.Status.WIN,
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestArchivePipelineItemView(APITestMixin):
    """Test archive and unarchive pipeline item."""

    def test_archive_without_reason(self):
        """Test pipeline item archive won't work without reason."""
        company = CompanyFactory()
        item = PipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.IN_PROGRESS,
        )
        url = _pipeline_item_archive_url(item.pk)
        response = self.api_client.post(
            url,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert response.data == {
            'reason': ['This field is required.'],
        }

    @freeze_time('2017-04-19 15:25:30.986208')
    def test_archive_with_reason(self):
        """Test pipeline item archive."""
        company = CompanyFactory()
        item = PipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.IN_PROGRESS,
        )
        url = _pipeline_item_archive_url(item.pk)
        response = self.api_client.post(
            url,
            data={'reason': 'foo'},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data == {
            'company': {
                'id': str(company.pk),
                'name': company.name,
                'turnover': company.turnover,
                'export_potential': company.export_potential,
            },
            'id': str(item.id),
            'name': item.name,
            'status': item.status,
            'created_on': format_date_or_datetime(item.created_on),
            'modified_on': format_date_or_datetime(item.modified_on),
            'contact': {
                'id': str(item.contact.pk),
                'name': item.contact.name,
            },
            'sector': {
                'id': str(item.sector.pk),
                'segment': item.sector.segment,
            },
            'potential_value': str(item.potential_value),
            'likelihood_to_win': item.likelihood_to_win,
            'expected_win_date': format_date_or_datetime(item.expected_win_date),
            'archived': True,
            'archived_on': '2017-04-19T15:25:30.986208Z',
            'archived_reason': 'foo',
        }

    def test_archive_wrong_method(self):
        """Test that GET requests to the archive endpoint fail."""
        company = CompanyFactory()
        item = PipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.IN_PROGRESS,
        )
        url = _pipeline_item_archive_url(item.pk)
        response = self.api_client.get(
            url,
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_unarchive(self):
        """Test pipeline item unarchive."""
        company = CompanyFactory()
        item = ArchivedPipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.IN_PROGRESS,
        )
        url = _pipeline_item_unarchive_url(item.pk)
        response = self.api_client.post(
            url,
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data == {
            'company': {
                'id': str(company.pk),
                'name': company.name,
                'turnover': company.turnover,
                'export_potential': company.export_potential,
            },
            'id': str(item.id),
            'name': item.name,
            'status': item.status,
            'created_on': format_date_or_datetime(item.created_on),
            'modified_on': format_date_or_datetime(item.modified_on),
            'contact': {
                'id': str(item.contact.pk),
                'name': item.contact.name,
            },
            'sector': {
                'id': str(item.sector.pk),
                'segment': item.sector.segment,
            },
            'potential_value': str(item.potential_value),
            'likelihood_to_win': item.likelihood_to_win,
            'expected_win_date': format_date_or_datetime(item.expected_win_date),
            'archived': False,
            'archived_on': None,
            'archived_reason': '',
        }

    def test_unarchive_wrong_method(self):
        """Test that GET requests to the unarchive endpoint fail."""
        company = CompanyFactory()
        item = ArchivedPipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.IN_PROGRESS,
        )
        url = _pipeline_item_unarchive_url(item.pk)
        response = self.api_client.get(
            url,
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestGetPipelineItemView(APITestMixin):
    """Tests for getting a single pipeline item."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        url = _pipeline_item_detail_url(uuid4())

        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['change_pipelineitem'], status.HTTP_403_FORBIDDEN),
            (['view_pipelineitem'], status.HTTP_200_OK),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status, api_client):
        """Test that the expected status is returned for various user permissions."""
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)
        item = PipelineItemFactory(adviser=user)
        url = _pipeline_item_detail_url(item.pk)

        api_client = self.create_api_client(user=user)
        response = api_client.get(url)
        assert response.status_code == expected_status

    def test_returns_404_if_pipeline_item_doesnt_exist(self):
        """Test that a 404 is returned if the pipeline item doesn't exist."""
        url = _pipeline_item_detail_url(uuid4())
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_can_get_a_pipeline_item(self):
        """Test that details of a single list can be retrieved."""
        company = CompanyFactory()
        item = PipelineItemFactory(adviser=self.user, company=company)
        url = _pipeline_item_detail_url(item.pk)

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data == {
            'company': {
                'id': str(company.pk),
                'name': company.name,
                'turnover': company.turnover,
                'export_potential': company.export_potential,
            },
            'id': str(item.id),
            'name': item.name,
            'status': item.status,
            'created_on': format_date_or_datetime(item.created_on),
            'modified_on': format_date_or_datetime(item.modified_on),
            'contact': {
                'id': str(item.contact.pk),
                'name': item.contact.name,
            },
            'sector': {
                'id': str(item.sector.pk),
                'segment': item.sector.segment,
            },
            'potential_value': str(item.potential_value),
            'likelihood_to_win': item.likelihood_to_win,
            'expected_win_date': format_date_or_datetime(item.expected_win_date),
            'archived': False,
            'archived_on': None,
            'archived_reason': None,
        }

    def test_can_get_an_archived_pipeline_item(self):
        """Test that details of a single archived item can be retrieved."""
        company = CompanyFactory()
        item = ArchivedPipelineItemFactory(adviser=self.user, company=company)
        url = _pipeline_item_detail_url(item.pk)

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data == {
            'company': {
                'id': str(company.pk),
                'name': company.name,
                'turnover': company.turnover,
                'export_potential': company.export_potential,
            },
            'id': str(item.id),
            'name': item.name,
            'status': item.status,
            'created_on': format_date_or_datetime(item.created_on),
            'modified_on': format_date_or_datetime(item.modified_on),
            'contact': {
                'id': str(item.contact.pk),
                'name': item.contact.name,
            },
            'sector': {
                'id': str(item.sector.pk),
                'segment': item.sector.segment,
            },
            'potential_value': str(item.potential_value),
            'likelihood_to_win': item.likelihood_to_win,
            'expected_win_date': format_date_or_datetime(item.expected_win_date),
            'archived': True,
            'archived_on': format_date_or_datetime(item.archived_on),
            'archived_reason': str(item.archived_reason),
        }

    def test_cannot_get_another_users_list(self):
        """Test that another user's list can't be retrieved."""
        item = PipelineItemFactory()
        url = _pipeline_item_detail_url(item.pk)

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
