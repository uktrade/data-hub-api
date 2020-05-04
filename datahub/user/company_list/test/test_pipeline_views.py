from uuid import uuid4

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import ArchivedCompanyFactory, CompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime
from datahub.user.company_list.models import PipelineItem
from datahub.user.company_list.test.factories import PipelineItemFactory

pipeline_collection_url = reverse('api-v4:company-list:pipelineitem-collection')


def _pipeline_item_detail_url(item_pk):
    return reverse('api-v4:company-list:pipelineitem-detail', kwargs={'pk': item_pk})


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

    def test_can_retrieve_multiple_pipeline_items_in_desc_order(self):
        """Test that details of multiple pipeline items can be retrieved."""
        company_1 = CompanyFactory()
        company_2 = CompanyFactory()
        company_3 = CompanyFactory()
        item_1 = PipelineItemFactory(
            adviser=self.user,
            company=company_1,
            status=PipelineItem.Status.WIN,
        )
        item_2 = PipelineItemFactory(
            adviser=self.user,
            company=company_2,
            status=PipelineItem.Status.IN_PROGRESS,
        )
        item_3 = PipelineItemFactory(
            adviser=self.user,
            company=company_3,
            status=PipelineItem.Status.LEADS,
        )
        response = self.api_client.get(pipeline_collection_url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 3

        self._assert_get_pipeline_items_response(
            response_data['results'][0],
            company_3,
            item_3,
        )
        self._assert_get_pipeline_items_response(
            response_data['results'][1],
            company_2,
            item_2,
        )
        self._assert_get_pipeline_items_response(
            response_data['results'][2],
            company_1,
            item_1,
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
        }


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
                    'company': '',
                    'status': '',
                },
                {
                    'company': ['This field may not be null.'],
                    'status': ['"" is not a valid choice.'],
                },
                id='company and status are empty strings',
            ),
            pytest.param(
                {
                    'company': '',
                    'status': PipelineItem.Status.LEADS,
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

    @freeze_time('2017-04-19 15:25:30.986208')
    def test_successfully_create_a_pipeline_item(self):
        """Test that a pipeline item can be created."""
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
            'status': pipeline_status,
            'created_on': '2017-04-19T15:25:30.986208Z',
        }

        pipeline_item = PipelineItem.objects.get(pk=response_data['id'])

        # adviser should be set to the authenticated user
        assert pipeline_item.adviser == self.user
        assert pipeline_item.created_by == self.user
        assert pipeline_item.modified_by == self.user

    @freeze_time('2017-04-19 15:25:30.986208')
    def test_successfully_create_a_pipeline_item_no_name(self):
        """Test that a pipeline item can be created even if name is not given."""
        company = CompanyFactory()
        pipeline_status = PipelineItem.Status.LEADS
        response = self.api_client.post(
            pipeline_collection_url,
            data={
                'company': str(company.pk),
                'status': pipeline_status,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'name': None,
            'company': {
                'id': str(company.pk),
                'name': company.name,
                'export_potential': company.export_potential,
                'turnover': company.turnover,
            },
            'status': pipeline_status,
            'created_on': '2017-04-19T15:25:30.986208Z',
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
                    'name': 'Bat',
                },
                ['"name" is not allowed to be updated.'],
                id='name is not allowed to be updated',
            ),
            pytest.param(
                {
                    'name': 'Man',
                    'status': 'win',
                },
                ['"name" is not allowed to be updated.'],
                id='name is not allowed to be updated',
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

    def test_patch_a_pipeline_item(self):
        """Test that status of a pipeline item can be patched."""
        company = CompanyFactory()
        item = PipelineItemFactory(
            adviser=self.user,
            company=company,
            status=PipelineItem.Status.WIN,
        )
        url = _pipeline_item_detail_url(item.pk)
        new_status = PipelineItem.Status.LEADS
        response = self.api_client.patch(
            url,
            data={
                'status': new_status,
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
            'name': item.name,
            'status': new_status,
            'created_on': format_date_or_datetime(item.created_on),
        }

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

    def test_returns_404_if_list_doesnt_exist(self):
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
        }

    def test_cannot_get_another_users_list(self):
        """Test that another user's list can't be retrieved."""
        item = PipelineItemFactory()
        url = _pipeline_item_detail_url(item.pk)

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
