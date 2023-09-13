import pytest

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import Objective
from datahub.company.test.factories import AdviserFactory, CompanyFactory, ObjectiveFactory
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_date_or_datetime,
)


class BaseObjectivesTests(APITestMixin):
    def user_api_client(self):
        """Create an api client where the user is the authenticated user"""
        user = create_test_user(
            permission_codenames=(
                'view_company',
                'view_objective',
            ),
        )
        return self.create_api_client(user)

    def adviser_api_client(self, adviser):
        """Create an api client where the adviser is the authenticated user"""
        return self.create_api_client(user=adviser)


class TestGettingObjectivesForCompany(BaseObjectivesTests):
    """Tests to retrieve a single objective for a company."""

    def test_company_has_no_objectives(self):
        company = CompanyFactory()
        url = reverse('api-v4:objective:list', kwargs={'company_id': company.id})
        response = self.user_api_client().get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 0

    def test_company_has_objectives(self):
        ObjectiveFactory()
        objective1 = ObjectiveFactory()
        ObjectiveFactory()
        objective2 = ObjectiveFactory(company=objective1.company)

        url = reverse('api-v4:objective:list', kwargs={'company_id': objective1.company.id})
        response = self.user_api_client().get(url)

        expected_ids = {str(objective1.id), str(objective2.id)}
        actual_ids = {result['id'] for result in response.json()['results']}
        assert expected_ids == actual_ids
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 2

    def test_company_objectives_default_ordering(self):
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
        response = self.user_api_client().get(url)

        expected_ids = {
            str(earliest_objective.id),
            str(middle_objective.id),
            str(latest_objective.id),
        }
        actual_ids = {result['id'] for result in response.json()['results']}

        assert expected_ids == actual_ids
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize('archived', ((True), (False), (None)))
    def test_company_objectives_archived_filtering(self, archived):
        archived_objective = ObjectiveFactory(archived=True)
        not_archived_objective = ObjectiveFactory(
            company=archived_objective.company,
            archived=False,
        )

        url = reverse(
            'api-v4:objective:list',
            kwargs={'company_id': archived_objective.company.id},
        )
        response = self.user_api_client().get(f'{url}?archived={archived}')

        expected_ids = (
            {str(archived_objective.id), str(not_archived_objective.id)}
            if archived is None
            else {
                str(archived_objective.id) if archived else str(not_archived_objective.id),
            }
        )
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


class TestGettingASingleObjective(BaseObjectivesTests):
    def test_view_objective(self):
        objective1 = ObjectiveFactory()

        url = reverse(
            'api-v4:objective:detail',
            kwargs={'company_id': objective1.company.id, 'pk': objective1.id},
        )
        response = self.user_api_client().get(url)

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
            'modified_by': {
                'id': str(objective1.modified_by.id),
                'first_name': objective1.modified_by.first_name,
                'last_name': objective1.modified_by.last_name,
                'name': objective1.modified_by.name,
            },
            'modified_on': format_date_or_datetime(objective1.modified_on),
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_response


class TestGettingObjectivesArchivedCountForCompany(BaseObjectivesTests):
    """Tests to retrieve the archived count of objectives"""

    def test_company_has_no_objectives(self):
        company = CompanyFactory()
        url = reverse('api-v4:objective:count', kwargs={'company_id': company.id})
        response = self.user_api_client().get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'archived_count': 0, 'not_archived_count': 0}

    def test_company_has_objectives(self):
        company = CompanyFactory()
        archived_objectives = ObjectiveFactory.create_batch(3, company=company, archived=True)
        not_archived_objectives = ObjectiveFactory.create_batch(5, company=company, archived=False)

        url = reverse('api-v4:objective:count', kwargs={'company_id': company.id})
        response = self.user_api_client().get(url)

        assert response.json() == {
            'archived_count': len(archived_objectives),
            'not_archived_count': len(not_archived_objectives),
        }
        assert response.status_code == status.HTTP_200_OK


class TestArchiveObjective(BaseObjectivesTests):
    """Test the archive POST endpoint for objective"""

    def test_archive_objective_without_reason_returns_bad_request(self):
        objective = ObjectiveFactory()

        url = reverse('api-v4:objective:archive', kwargs={'pk': objective.id})

        response = self.user_api_client().post(url, data={})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'reason': ['This field is required.'],
        }

    def test_archive_objective_with_valid_reason_returns_success(self):
        adviser = AdviserFactory()
        objective = ObjectiveFactory(created_by=adviser)

        url = reverse('api-v4:objective:archive', kwargs={'pk': objective.id})

        response = self.adviser_api_client(adviser).post(url, data={'reason': 'completed'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived']
        assert response.data['archived_by'] == {
            'id': str(adviser.id),
            'first_name': adviser.first_name,
            'last_name': adviser.last_name,
            'name': adviser.name,
        }
        assert response.data['archived_reason'] == 'completed'
        assert response.data['id'] == str(objective.id)
