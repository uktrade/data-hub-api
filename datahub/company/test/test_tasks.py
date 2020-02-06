import logging
from unittest import mock

import pytest
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from freezegun import freeze_time

from datahub.company.constants import AUTOMATIC_COMPANY_ARCHIVE_FEATURE_FLAG
from datahub.company.models import Company
from datahub.company.tasks import automatic_company_archive
from datahub.company.test.factories import CompanyFactory
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.investor_profile.test.factories import LargeCapitalInvestorProfileFactory
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.omis.order.test.factories import OrderFactory


@pytest.fixture()
def automatic_company_archive_feature_flag():
    """
    Creates the automatic company archive feature flag.
    """
    yield FeatureFlagFactory(code=AUTOMATIC_COMPANY_ARCHIVE_FEATURE_FLAG)


@pytest.mark.django_db
class TestAutomaticCompanyArchive:
    """
    Tests for the automatic_company_archive task.
    """

    def test_no_feature_flag(
        self,
        caplog,
    ):
        """
        Test that if the feature flag is not enabled, the
        task will not run.
        """
        caplog.set_level(logging.INFO, logger='datahub.company.tasks')
        automatic_company_archive.apply_async(kwargs={'simulate': False})
        assert caplog.messages == [
            f'Feature flag "{AUTOMATIC_COMPANY_ARCHIVE_FEATURE_FLAG}" is not active, exiting.',
        ]

    @pytest.mark.parametrize(
        'lock_acquired, call_count',
        (
            (False, 0),
            (True, 1),
        ),
    )
    def test_lock(
        self,
        monkeypatch,
        automatic_company_archive_feature_flag,
        lock_acquired,
        call_count,
    ):
        """
        Test that the task doesn't run if it cannot acquire
        the advisory_lock.
        """
        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.company.tasks.advisory_lock',
            mock_advisory_lock,
        )
        mock_automatic_company_archive = mock.Mock()
        monkeypatch.setattr(
            'datahub.company.tasks._automatic_company_archive',
            mock_automatic_company_archive,
        )
        automatic_company_archive()
        assert mock_automatic_company_archive.call_count == call_count

    @pytest.mark.parametrize(
        'simulate',
        (
            True,
            False,
        ),
    )
    @freeze_time('2020-01-01-12:00:00')
    def test_no_interactions(
        self,
        caplog,
        automatic_company_archive_feature_flag,
        simulate,
    ):
        """
        Test that a company without interaction that fits
        all the other criteria is archived.
        """
        caplog.set_level(logging.INFO, logger='datahub.company.tasks')
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        with freeze_time(gt_3m_ago):
            company = CompanyFactory()
        task_result = automatic_company_archive.apply_async(
            kwargs={'simulate': simulate},
        )
        company.refresh_from_db()
        if simulate:
            assert caplog.messages == [
                f'[SIMULATION] Automatically archived company: {company.id}',
            ]
        else:
            assert task_result.successful()
            assert company.archived
            assert caplog.messages == [
                f'Automatically archived company: {company.id}',
            ]

    @pytest.mark.parametrize(
        'interaction_date_delta, expected_archived',
        (
            (relativedelta(), False),
            (relativedelta(years=8), False),
            (relativedelta(years=8, days=1), True),
        ),
    )
    @freeze_time('2020-01-01-12:00:00')
    def test_interactions(
        self,
        automatic_company_archive_feature_flag,
        interaction_date_delta,
        expected_archived,
    ):
        """
        Test that a company with interactions on various dates
        around the 8y boundary are archived or not as expected.
        """
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        with freeze_time(gt_3m_ago):
            company = CompanyFactory()
        CompanyInteractionFactory(
            company=company,
            date=timezone.now() - interaction_date_delta,
        )
        task_result = automatic_company_archive.apply_async(
            kwargs={'simulate': False},
        )
        assert task_result.successful()
        company.refresh_from_db()
        assert company.archived == expected_archived

    @pytest.mark.parametrize(
        'created_on_delta, expected_archived',
        (
            (relativedelta(), False),
            (relativedelta(months=3), False),
            (relativedelta(months=3, days=1), True),
        ),
    )
    @freeze_time('2020-01-01-12:00:00')
    def test_created_on(
        self,
        automatic_company_archive_feature_flag,
        created_on_delta,
        expected_archived,
    ):
        """
        Test that a company created_on dates around the 3m boundary
        are archived or not as expected.
        """
        created_on = timezone.now() - created_on_delta
        with freeze_time(created_on):
            company = CompanyFactory()
        CompanyInteractionFactory(
            company=company,
            date=timezone.now() - relativedelta(years=8, days=1),
        )
        task_result = automatic_company_archive.apply_async(kwargs={'simulate': False})
        assert task_result.successful()
        company.refresh_from_db()
        assert company.archived == expected_archived

    @pytest.mark.parametrize(
        'modified_on_delta, expected_archived',
        (
            (relativedelta(), False),
            (relativedelta(months=3), False),
            (relativedelta(months=3, days=1), True),
        ),
    )
    @freeze_time('2020-01-01-12:00:00')
    def test_modified_on(
        self,
        automatic_company_archive_feature_flag,
        modified_on_delta,
        expected_archived,
    ):
        """
        Test that a company modified_on dates around the 3m boundary
        are archived or not as expected.
        """
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        with freeze_time(gt_3m_ago):
            company = CompanyFactory()
        CompanyInteractionFactory(
            company=company,
            date=timezone.now() - relativedelta(years=8, days=1),
        )
        with freeze_time(timezone.now() - modified_on_delta):
            company.save()
        task_result = automatic_company_archive.apply_async(kwargs={'simulate': False})
        assert task_result.successful()
        archived_company = Company.objects.get(pk=company.id)
        assert archived_company.archived == expected_archived
        assert archived_company.modified_on == company.modified_on

    @freeze_time('2020-01-01-12:00:00')
    def test_orders(
        self,
        automatic_company_archive_feature_flag,
    ):
        """
        Test that a company with OMIS orders is not archived.
        """
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        with freeze_time(gt_3m_ago):
            company = CompanyFactory()
        OrderFactory(company=company)
        task_result = automatic_company_archive.apply_async(kwargs={'simulate': False})
        assert task_result.successful()
        company.refresh_from_db()
        assert not company.archived

    @freeze_time('2020-01-01-12:00:00')
    def test_limit(
        self,
        automatic_company_archive_feature_flag,
    ):
        """
        Test that we can set a limit to the number of companies
        that are automatically archived.
        """
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        with freeze_time(gt_3m_ago):
            companies = CompanyFactory.create_batch(3)
        task_result = automatic_company_archive.apply_async(
            kwargs={
                'simulate': False,
                'limit': 2,
            },
        )
        assert task_result.successful()

        archived_companies_count = 0
        for company in companies:
            company.refresh_from_db()
            if company.archived:
                archived_companies_count += 1

        assert archived_companies_count == 2

    @freeze_time('2020-01-01-12:00:00')
    def test_investor_profile(
        self,
        automatic_company_archive_feature_flag,
    ):
        """
        Test that a company with investor profile is not archived.
        """
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        with freeze_time(gt_3m_ago):
            companies = CompanyFactory.create_batch(2)
        LargeCapitalInvestorProfileFactory(investor_company=companies[0])
        task_result = automatic_company_archive.apply_async(kwargs={'simulate': False})
        assert task_result.successful()

        archived_companies_count = 0
        for company in companies:
            company.refresh_from_db()
            if company.archived:
                archived_companies_count += 1

        assert archived_companies_count == 1

    @pytest.mark.parametrize(
        'investment_projects_status, expected_archived',
        (
            (
                [InvestmentProject.Status.LOST],
                True,
            ),
            (
                [InvestmentProject.Status.LOST, InvestmentProject.Status.ONGOING],
                False,
            ),
            (
                [InvestmentProject.Status.ONGOING],
                False,
            ),
            (
                [],
                True,
            ),
        ),
    )
    @freeze_time('2020-01-01-12:00:00')
    def test_investment_projects(
        self,
        automatic_company_archive_feature_flag,
        investment_projects_status,
        expected_archived,
    ):
        """
        Test that a company with active investment projects is not
        archived.
        """
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        with freeze_time(gt_3m_ago):
            company = CompanyFactory()
        for status in investment_projects_status:
            InvestmentProjectFactory(investor_company=company, status=status)
        task_result = automatic_company_archive.apply_async(kwargs={'simulate': False})
        assert task_result.successful()
        company.refresh_from_db()
        assert company.archived == expected_archived
