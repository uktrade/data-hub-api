import logging
from unittest import mock

import pytest
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from freezegun import freeze_time

from datahub.company.constants import AUTOMATIC_COMPANY_ARCHIVE_FEATURE_FLAG
from datahub.company.models import Company
from datahub.company.tasks.company import schedule_automatic_company_archive
from datahub.company.test.factories import CompanyFactory
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.investor_profile.test.factories import LargeCapitalInvestorProfileFactory
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.omis.order.test.factories import OrderFactory


@pytest.fixture
def automatic_company_archive_feature_flag():
    """Creates the automatic company archive feature flag.
    """
    return FeatureFlagFactory(code=AUTOMATIC_COMPANY_ARCHIVE_FEATURE_FLAG)


@pytest.mark.django_db
class TestAutomaticCompanyArchive:
    """Tests for the automatic_company_archive task.
    """

    def test_no_feature_flag(
        self,
        caplog,
    ):
        """Test that if the feature flag is not enabled, the
        task will not run.
        """
        caplog.set_level(logging.INFO, logger='datahub.company.tasks.company')
        job = schedule_automatic_company_archive(simulate=False)
        assert caplog.messages == [
            'Feature flag "automatic-company-archive" is not active, exiting.',
            f'Task {job.id} automatic_company_archive '
            'scheduled limited to 1000 and simulate set to False',
        ]

    @pytest.mark.parametrize(
        ('lock_acquired', 'call_count'),
        [
            (False, 0),
            (True, 1),
        ],
    )
    def test_lock(
        self,
        monkeypatch,
        automatic_company_archive_feature_flag,
        lock_acquired,
        call_count,
    ):
        """Test that the task doesn't run if it cannot acquire
        the advisory_lock.
        """
        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.company.tasks.company.advisory_lock',
            mock_advisory_lock,
        )
        mock_automatic_company_archive = mock.Mock()
        monkeypatch.setattr(
            'datahub.company.tasks.company._automatic_company_archive',
            mock_automatic_company_archive,
        )
        schedule_automatic_company_archive()
        assert mock_automatic_company_archive.call_count == call_count

    @pytest.mark.parametrize(
        'simulate',
        [
            True,
            False,
        ],
    )
    @freeze_time('2020-01-01-12:00:00')
    def test_no_interactions(
        self,
        caplog,
        automatic_company_archive_feature_flag,
        simulate,
    ):
        """Test that a company without interaction that fits
        all the other criteria is archived.
        """
        caplog.set_level(logging.INFO, logger='datahub.company.tasks.company')
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        with freeze_time(gt_3m_ago):
            company = CompanyFactory()
        job = schedule_automatic_company_archive(simulate=simulate)
        company.refresh_from_db()
        if simulate:
            assert caplog.messages == [
                f'[SIMULATION] Automatically archived company: {company.id}',
                f'Task {job.id} automatic_company_archive '
                'scheduled limited to 1000 and simulate set to True',
            ]
        else:
            assert company.archived
            assert caplog.messages == [
                f'Automatically archived company: {company.id}',
                f'Task {job.id} automatic_company_archive '
                'scheduled limited to 1000 and simulate set to False',
            ]

    @pytest.mark.parametrize(
        ('interaction_date_delta', 'expected_archived'),
        [
            (relativedelta(), False),
            (relativedelta(years=5), False),
            (relativedelta(years=5, days=1), True),
        ],
    )
    @freeze_time('2020-01-01-12:00:00')
    def test_interactions(
        self,
        automatic_company_archive_feature_flag,
        interaction_date_delta,
        expected_archived,
    ):
        """Test that a company with interactions on various dates
        around the 8y boundary are archived or not as expected.
        """
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        with freeze_time(gt_3m_ago):
            company = CompanyFactory()
        CompanyInteractionFactory(
            company=company,
            date=timezone.now() - interaction_date_delta,
        )
        schedule_automatic_company_archive(simulate=False)
        company.refresh_from_db()
        assert company.archived == expected_archived

    @pytest.mark.parametrize(
        ('created_on_delta', 'expected_archived'),
        [
            (relativedelta(), False),
            (relativedelta(months=3), False),
            (relativedelta(months=3, days=1), True),
        ],
    )
    @freeze_time('2020-01-01-12:00:00')
    def test_created_on(
        self,
        automatic_company_archive_feature_flag,
        created_on_delta,
        expected_archived,
    ):
        """Test that a company created_on dates around the 3m boundary
        are archived or not as expected.
        """
        created_on = timezone.now() - created_on_delta
        with freeze_time(created_on):
            company = CompanyFactory()
        CompanyInteractionFactory(
            company=company,
            date=timezone.now() - relativedelta(years=8, days=1),
        )
        schedule_automatic_company_archive(simulate=False)
        company.refresh_from_db()
        assert company.archived == expected_archived

    @pytest.mark.parametrize(
        ('created_on_delta', 'companies_to_create', 'expected_message'),
        [
            (
                relativedelta(),
                1,
                'datahub.company.tasks.automatic_company_archive archived: 0',
            ),
            (
                relativedelta(months=3, days=1),
                1,
                'datahub.company.tasks.automatic_company_archive archived: 1',
            ),
            (
                relativedelta(months=3, days=1),
                3,
                'datahub.company.tasks.automatic_company_archive archived: 3',
            ),
        ],
    )
    @freeze_time('2020-01-01-12:00:00')
    def test_realtime_messages_sent(
        self,
        monkeypatch,
        automatic_company_archive_feature_flag,
        created_on_delta,
        companies_to_create,
        expected_message,
    ):
        """Test that appropriate realtime messaging is sent which reflects the archiving
        actions.
        """
        created_on = timezone.now() - created_on_delta
        for _ in range(companies_to_create):
            with freeze_time(created_on):
                company = CompanyFactory()
            CompanyInteractionFactory(
                company=company,
                date=timezone.now() - relativedelta(years=8, days=1),
            )
        mock_send_realtime_message = mock.Mock()
        monkeypatch.setattr(
            'datahub.company.tasks.company.send_realtime_message',
            mock_send_realtime_message,
        )

        schedule_automatic_company_archive(simulate=False)

        mock_send_realtime_message.assert_called_once_with(expected_message)

    @pytest.mark.parametrize(
        ('modified_on_delta', 'expected_archived'),
        [
            (relativedelta(), False),
            (relativedelta(months=3), False),
            (relativedelta(months=3, days=1), True),
        ],
    )
    @freeze_time('2020-01-01-12:00:00')
    def test_modified_on(
        self,
        automatic_company_archive_feature_flag,
        modified_on_delta,
        expected_archived,
    ):
        """Test that a company modified_on dates around the 3m boundary
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

        schedule_automatic_company_archive(simulate=False)

        archived_company = Company.objects.get(pk=company.id)
        assert archived_company.archived == expected_archived
        assert archived_company.modified_on == company.modified_on

    @freeze_time('2020-01-01-12:00:00')
    def test_orders(
        self,
        automatic_company_archive_feature_flag,
    ):
        """Test that a company with OMIS orders is not archived.
        """
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        with freeze_time(gt_3m_ago):
            company = CompanyFactory()
        OrderFactory(company=company)
        schedule_automatic_company_archive(simulate=False)
        company.refresh_from_db()
        assert not company.archived

    @freeze_time('2020-01-01-12:00:00')
    def test_limit(
        self,
        automatic_company_archive_feature_flag,
    ):
        """Test that we can set a limit to the number of companies
        that are automatically archived.
        """
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        with freeze_time(gt_3m_ago):
            companies = CompanyFactory.create_batch(3)
        schedule_automatic_company_archive(
            simulate=False,
            limit=2,
        )

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
        """Test that a company with investor profile is not archived.
        """
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        with freeze_time(gt_3m_ago):
            companies = CompanyFactory.create_batch(2)
        LargeCapitalInvestorProfileFactory(investor_company=companies[0])
        schedule_automatic_company_archive(simulate=False)

        archived_companies_count = 0
        for company in companies:
            company.refresh_from_db()
            if company.archived:
                archived_companies_count += 1

        assert archived_companies_count == 1

    @pytest.mark.parametrize(
        ('investment_projects_status', 'expected_archived'),
        [
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
        ],
    )
    @freeze_time('2020-01-01-12:00:00')
    def test_investment_projects(
        self,
        automatic_company_archive_feature_flag,
        investment_projects_status,
        expected_archived,
    ):
        """Test that a company with active investment projects is not
        archived.
        """
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        with freeze_time(gt_3m_ago):
            company = CompanyFactory()
        for status in investment_projects_status:
            InvestmentProjectFactory(investor_company=company, status=status)

        schedule_automatic_company_archive(simulate=False)

        company.refresh_from_db()
        assert company.archived == expected_archived

    @freeze_time('2020-01-01-12:00:00')
    def test_active_company_with_global_ultimate_duns_not_archived(
        self,
        automatic_company_archive_feature_flag,
    ):
        """Test companies that share an global_ultimate_duns_number
        are not archived if any of them are active.
        """
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        global_ultimate_duns_number = '123456789'
        with freeze_time(gt_3m_ago):
            company_global_ultimate = CompanyFactory(
                duns_number=global_ultimate_duns_number,
                global_ultimate_duns_number=global_ultimate_duns_number,
            )
            company_1 = CompanyFactory(global_ultimate_duns_number=global_ultimate_duns_number)
        company_2 = CompanyFactory(global_ultimate_duns_number=global_ultimate_duns_number)

        schedule_automatic_company_archive(simulate=False)
        company_global_ultimate.refresh_from_db()
        company_1.refresh_from_db()
        company_2.refresh_from_db()

        assert not company_global_ultimate.archived
        assert not company_1.archived
        assert not company_2.archived

    @freeze_time('2020-01-01-12:00:00')
    def test_active_company_with_global_ultimate_duns_archived(
        self,
        automatic_company_archive_feature_flag,
    ):
        """Test companies that share an global_ultimate_duns_number
        can be archived if none of them are active.
        """
        gt_3m_ago = timezone.now() - relativedelta(months=3, days=1)
        global_ultimate_duns_number = '123456789'
        with freeze_time(gt_3m_ago):
            company_global_ultimate = CompanyFactory(
                duns_number=global_ultimate_duns_number,
                global_ultimate_duns_number=global_ultimate_duns_number,
            )
            company_1 = CompanyFactory(global_ultimate_duns_number=global_ultimate_duns_number)
            company_2 = CompanyFactory(global_ultimate_duns_number=global_ultimate_duns_number)

        schedule_automatic_company_archive(simulate=False)
        company_global_ultimate.refresh_from_db()
        company_1.refresh_from_db()
        company_2.refresh_from_db()

        assert company_global_ultimate.archived
        assert company_1.archived
        assert company_2.archived
