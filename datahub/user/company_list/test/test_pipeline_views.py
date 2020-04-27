import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory

from datahub.user.company_list.models import PipelineItem
from datahub.user.company_list.test.factories import PipelineItemFactory

from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime


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
        pipeline_item = PipelineItemFactory(adviser=self.user, company=company)
        response = self.api_client.get(pipeline_collection_url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 1
        assert response_data['results'][0] == {
            'company': {
                'id': str(company.pk),
                'name': company.name,
                'turnover': company.turnover,
                'export_potential': company.export_potential,
            },
            'status': pipeline_item.status,
            'created_on': format_date_or_datetime(pipeline_item.created_on),
        }

    def test_can_retrieve_multiple_pipeline_items(self):
        """Test that details of multiple pipeline items can be retrieved."""
        company_1 = CompanyFactory()
        company_2 = CompanyFactory()
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
        response = self.api_client.get(pipeline_collection_url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data['results']) == 2
        assert response_data['results'][0] == {
            'company': {
                'id': str(company_1.pk),
                'name': company_1.name,
                'turnover': company_1.turnover,
                'export_potential': company_1.export_potential,
            },
            'status': item_1.status,
            'created_on': format_date_or_datetime(item_1.created_on),
        }
        assert response_data['results'][1] == {
            'company': {
                'id': str(company_2.pk),
                'name': company_2.name,
                'turnover': company_2.turnover,
                'export_potential': company_2.export_potential,
            },
            'status': item_2.status,
            'created_on': format_date_or_datetime(item_2.created_on),
        }

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
        assert response_data['results'][0] == {
            'company': {
                'id': str(company.pk),
                'name': company.name,
                'turnover': company.turnover,
                'export_potential': company.export_potential,
            },
            'status': PipelineItem.Status.WIN,
        }
