import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime
from datahub.user.company_list.models import PipelineItem
from datahub.user.company_list.test.factories import PipelineItemFactory


pipeline_collection_url = reverse('api-v4:company-list:pipelineitem-collection')


class TestGetPipelineItemView(APITestMixin):
    """Tests for getting pipeline items."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        response = api_client.get(pipeline_collection_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['view_pipelineitem'], status.HTTP_403_FORBIDDEN),
            (['view_company', 'view_pipelineitem'], status.HTTP_200_OK),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status, api_client):
        """Test that the expected status is returned for various user permissions."""
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)
        PipelineItemFactory(adviser=user)

        api_client = self.create_api_client(user=user)
        response = api_client.get(pipeline_collection_url)
        assert response.status_code == expected_status

    def test_returns_404_if_pipeline_doesnt_exist(self):
        """Test that a 404 is returned if the there are no pipeline items."""
        response = self.api_client.get(pipeline_collection_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

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

    def test_can_filter_by_valid_status(self):
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
            data={'status': PipelineItem.Status.IN_PROGRESS},
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 1
        assert response_data['results'][0]['status'] == PipelineItem.Status.IN_PROGRESS

    def test_returns_empty_list_when_filtering_non_existing_status(self):
        """Test that it can filter by status."""
        PipelineItemFactory(
            adviser=self.user,
            company=CompanyFactory(),
            status=PipelineItem.Status.WIN,
        )

        response = self.api_client.get(
            pipeline_collection_url,
            data={'status': PipelineItem.Status.LEADS},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['results'] == []

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

    def test_returns_404_when_specific_user_has_no_pipeline_items(self):
        """Test that another user's pipeline item can't be retrieved."""
        PipelineItemFactory()
        response = self.api_client.get(pipeline_collection_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

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
            'status': item.status,
            'created_on': format_date_or_datetime(item.created_on),
        }
