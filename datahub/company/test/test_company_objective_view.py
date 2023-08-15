import pytest

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import Objective
from datahub.company.test.factories import CompanyFactory, ObjectiveFactory
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_date_or_datetime,
)


class TestGettingObjectivesForCompany(APITestMixin):
    """Tests to retrieve a single objective for a company."""

    def test_company_has_no_objectives(self):
        user = create_test_user(
            permission_codenames=(
                'view_company',
                'view_objective',
            ),
        )
        company = CompanyFactory()
        url = reverse('api-v4:objective:list', kwargs={'company_id': company.id})
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 0

    def test_company_has_objectives(self):
        user = create_test_user(
            permission_codenames=(
                'view_company',
                'view_objective',
            ),
        )
        ObjectiveFactory()
        objective1 = ObjectiveFactory()
        ObjectiveFactory()
        objective2 = ObjectiveFactory(company=objective1.company)

        url = reverse('api-v4:objective:list', kwargs={'company_id': objective1.company.id})
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        expected_ids = {str(objective1.id), str(objective2.id)}
        actual_ids = {result['id'] for result in response.json()['results']}
        assert expected_ids == actual_ids
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 2

    def test_company_objectives_default_ordering(self):
        user = create_test_user(
            permission_codenames=(
                'view_company',
                'view_objective',
            ),
        )

        latest_objective = ObjectiveFactory(target_date='2030-06-06')
        middle_objective = ObjectiveFactory(
            company=latest_objective.company,
            target_date='2025-04-04',
        )
        earliest_objective = ObjectiveFactory(
            company=latest_objective.company,
            target_date='2020-02-02',
        )

        url = reverse(
            'api-v4:objective:list',
            kwargs={'company_id': earliest_objective.company.id},
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        expected_ids = {
            str(earliest_objective.id),
            str(middle_objective.id),
            str(latest_objective.id),
        }
        actual_ids = {result['id'] for result in response.json()['results']}

        assert expected_ids == actual_ids
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize('archived', ((True), (False)))
    def test_company_objectives_archived_filtering(self, archived):
        user = create_test_user(
            permission_codenames=(
                'view_company',
                'view_objective',
            ),
        )

        archived_objective = ObjectiveFactory(archived=True)
        not_archived_objective = ObjectiveFactory(
            company=archived_objective.company,
            archived=False,
        )

        url = reverse(
            'api-v4:objective:list',
            kwargs={'company_id': archived_objective.company.id},
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(f'{url}?archived={archived}')

        expected_ids = {
            str(archived_objective.id) if archived else str(not_archived_objective.id),
        }
        actual_ids = {result['id'] for result in response.json()['results']}

        assert expected_ids == actual_ids
        assert response.status_code == status.HTTP_200_OK


class TestAddCompanyObjective(APITestMixin):
    """Tests to add a single objective for a company."""

    def test_add_company_objective(self):
        company = CompanyFactory()
        post_data = {
            'subject': 'From a ways away',
            'detail': 'Get in touch and do the do',
            'target_date': '2024-11-29',
            'company': str(company.id),
            'has_blocker': True,
            'blocker_description': 'More words',
            'progress': 80,
        }
        url = reverse('api-v4:objective:list', kwargs={'company_id': company.id})
        response = self.api_client.post(
            url,
            data=post_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        database_objective = Objective.objects.get(pk=response_data['id'])
        assert post_data['subject'] == database_objective.subject


class TestAmendCompanyObjective(APITestMixin):
    """Tests to amend an existing company objective."""

    def test_amend_company_objective(self):
        objective = ObjectiveFactory(subject='Original subject', progress=10)
        patch_data = {
            'subject': 'Amended subject',
            'progress': 90,
        }
        url = reverse(
            'api-v4:objective:detail',
            kwargs={'company_id': objective.company.id, 'pk': objective.id},
        )
        response = self.api_client.patch(
            url,
            data=patch_data,
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        database_objective = Objective.objects.get(pk=response_data['id'])
        assert patch_data['subject'] == database_objective.subject
        assert patch_data['progress'] == database_objective.progress
        assert objective.subject != database_objective.subject
        assert objective.subject != database_objective.progress


class TestGettingASingleObjective(APITestMixin):
    def test_view_objective(self):
        user = create_test_user(
            permission_codenames=(
                'view_company',
                'view_objective',
            ),
        )
        objective1 = ObjectiveFactory()

        url = reverse(
            'api-v4:objective:detail',
            kwargs={'company_id': objective1.company.id, 'pk': objective1.id},
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        expected_response = {
            'id': str(objective1.id),
            'subject': objective1.subject,
            'detail': objective1.detail,
            'target_date': str(objective1.target_date),
            'company': {'id': str(objective1.company.id), 'name': objective1.company.name},
            'has_blocker': objective1.has_blocker,
            'blocker_description': objective1.blocker_description,
            'progress': objective1.progress,
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'created_on': format_date_or_datetime(objective1.created_on),
            'modified_by': None,
            'modified_on': format_date_or_datetime(objective1.modified_on),
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_response
