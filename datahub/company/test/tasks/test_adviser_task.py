import logging
from datetime import date, datetime
from unittest import mock
from uuid import uuid4

import pytest
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from datahub.company.tasks import automatic_adviser_deactivate
from datahub.company.tasks.adviser import schedule_automatic_adviser_deactivate
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    OneListCoreTeamMemberFactory,
)
from datahub.company_referral.test.factories import CompanyReferralFactory
from datahub.event.test.factories import EventFactory
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    ContactFactory,
    InteractionDITParticipantFactory,
)
from datahub.investment.opportunity.test.factories import LargeCapitalOpportunityFactory
from datahub.investment.project.test.factories import (
    InvestmentProjectFactory,
    InvestmentProjectTeamMemberFactory,
)
from datahub.omis.order.test.factories import OrderFactory


def deactivateable_adviser(**kwargs):
    """
    Creates and returns an adviser that is by default deactivatable

    The adviser is created just over two years ago. However, any keyword arguments
    are passed to the Adviser constructor, which can override this and other
    defaults. They would typically be used to make the adviser not deactivatable
    in tests
    """
    return AdviserFactory(**{
        'sso_user_id': None,
        'date_joined': date.today() - relativedelta(years=2, days=1),
        'is_active': True,
        **kwargs,
    })


@pytest.mark.django_db
class TestAdviserDeactivateTask:
    """
    Tests for the task that deactivate advisers
    """

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
        lock_acquired,
        call_count,
    ):
        """
        Test that the task doesn't run if it cannot acquire the advisory_lock
        """
        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.company.tasks.adviser.advisory_lock',
            mock_advisory_lock,
        )
        mock_automatic_adviser_deactivate = mock.Mock()
        monkeypatch.setattr(
            'datahub.company.tasks.adviser._automatic_adviser_deactivate',
            mock_automatic_adviser_deactivate,
        )
        automatic_adviser_deactivate()
        assert mock_automatic_adviser_deactivate.call_count == call_count

    def test_limit(self):
        """
        Test adviser deactivating query limit
        """
        limit = 2
        advisers = [deactivateable_adviser() for _ in range(3)]
        automatic_adviser_deactivate(limit=limit)

        count = 0
        for adviser in advisers:
            adviser.refresh_from_db()
            if adviser.is_active is False:
                count += 1
        assert count == limit

    @pytest.mark.parametrize('simulate', (True, False))
    def test_simulate(self, caplog, simulate):
        """
        Test adviser deactivating simulate flag
        """
        caplog.set_level(logging.INFO, logger='datahub.company.tasks.adviser')
        date = datetime.now() - relativedelta(days=10)
        with freeze_time(date):
            adviser1 = deactivateable_adviser()
        automatic_adviser_deactivate(simulate=simulate)
        adviser1.refresh_from_db()
        if simulate:
            assert caplog.messages == [
                f'[SIMULATION] Automatically de-activate adviser: {adviser1.id}',
            ]
        else:
            assert adviser1.is_active is False
            assert caplog.messages == [f'Automatically de-activate adviser: {adviser1.id}']

    @pytest.mark.parametrize(
        'advisers, message',
        (
            (
                (False, False, False),
                'datahub.company.tasks.automatic_adviser_deactivate deactivated: 0',
            ),
            (
                (False, False, True),
                'datahub.company.tasks.automatic_adviser_deactivate deactivated: 1',
            ),
            (
                (True, True, True),
                'datahub.company.tasks.automatic_adviser_deactivate deactivated: 3',
            ),
        ),
    )
    def test_realtime_messages_sent(
        self,
        monkeypatch,
        advisers,
        message,
    ):
        """
        Test that appropriate realtime messaging is sent which reflects the deactivating actions
        """
        for deactivate in advisers:
            deactivateable_adviser(is_active=deactivate)

        mock_send_realtime_message = mock.Mock()
        monkeypatch.setattr(
            'datahub.company.tasks.adviser.send_realtime_message',
            mock_send_realtime_message,
        )
        automatic_adviser_deactivate()
        mock_send_realtime_message.assert_called_once_with(message)

    def test_recently_joined_adviser_does_not_deactivate(self):
        """
        Test adviser does not deactivate if recently joined
        """
        with freeze_time('2017-02-21'):
            two_years_ago = date.today() - relativedelta(years=2)
            adviser1 = deactivateable_adviser()
            adviser2 = deactivateable_adviser(
                date_joined=two_years_ago - relativedelta(years=2, day=1))
            adviser3 = deactivateable_adviser(
                date_joined=two_years_ago)
            assert adviser1.is_active is True
            assert adviser2.is_active is True
            assert adviser3.is_active is True

            # run task twice expecting same result
            for _ in range(2):
                automatic_adviser_deactivate(limit=200)

                adviser1.refresh_from_db()
                adviser2.refresh_from_db()
                adviser3.refresh_from_db()
                assert adviser1.is_active is False
                assert adviser2.is_active is False
                assert adviser3.is_active is True

    def test_adviser_with_sso_id_does_not_dectivate(self):
        """
        Test adviser with an SSO ID does not deactivate

        The plan would be to have logic to properly deactivate these, but since
        we don't have this logic for now, we test that we don't deactivate these
        """
        with freeze_time('2017-02-21'):
            adviser1 = deactivateable_adviser()
            adviser2 = deactivateable_adviser(sso_user_id=None)
            adviser3 = deactivateable_adviser(sso_user_id=uuid4())
            assert adviser1.is_active is True
            assert adviser2.is_active is True
            assert adviser3.is_active is True

            # run task twice expecting same result
            for _ in range(2):
                automatic_adviser_deactivate(limit=200)

                adviser1.refresh_from_db()
                adviser2.refresh_from_db()
                adviser3.refresh_from_db()
                assert adviser1.is_active is False
                assert adviser2.is_active is False
                assert adviser3.is_active is True

    @pytest.mark.parametrize(
        'factory, attribute_name',
        (
            (CompanyInteractionFactory, 'created_by'),
            (CompanyInteractionFactory, 'modified_by'),
            (CompanyInteractionFactory, 'archived_by'),
            (InteractionDITParticipantFactory, 'adviser'),
            (CompanyReferralFactory, 'created_by'),
            (CompanyReferralFactory, 'modified_by'),
            (CompanyReferralFactory, 'completed_by'),
            (CompanyFactory, 'created_by'),
            (CompanyFactory, 'modified_by'),
            (CompanyFactory, 'archived_by'),
            (CompanyFactory, 'one_list_account_owner'),
            (CompanyFactory, 'transferred_by'),
            (ContactFactory, 'created_by'),
            (ContactFactory, 'modified_by'),
            (ContactFactory, 'archived_by'),
            (ContactFactory, 'adviser'),
            (OrderFactory, 'created_by'),
            (OrderFactory, 'modified_by'),
            (OrderFactory, 'completed_by'),
            (OrderFactory, 'cancelled_by'),
            (LargeCapitalOpportunityFactory, 'created_by'),
            (LargeCapitalOpportunityFactory, 'modified_by'),
            (InvestmentProjectFactory, 'created_by'),
            (InvestmentProjectFactory, 'modified_by'),
            (InvestmentProjectFactory, 'archived_by'),
            (InvestmentProjectFactory, 'client_relationship_manager'),
            (InvestmentProjectFactory, 'project_manager'),
            (InvestmentProjectFactory, 'project_manager_first_assigned_by'),
            (InvestmentProjectFactory, 'referral_source_adviser'),
            (InvestmentProjectFactory, 'project_assurance_adviser'),
            (EventFactory, 'created_by'),
            (EventFactory, 'modified_by'),
            (EventFactory, 'organiser'),
        ),
    )
    def test_adviser_with_recent_activity_does_not_deactivate(self, factory, attribute_name):
        """
        Test adviser with recent activity doesn't deactivate
        """
        with freeze_time('2017-02-21'):
            two_years_ago = date.today() - relativedelta(years=2)

            adviser1 = deactivateable_adviser()

            adviser2 = deactivateable_adviser()
            with freeze_time(two_years_ago - relativedelta(days=1)):
                factory(**{attribute_name: adviser2})

            adviser3 = deactivateable_adviser()
            with freeze_time(two_years_ago):
                factory(**{attribute_name: adviser3})

            assert adviser1.is_active is True
            assert adviser2.is_active is True
            assert adviser3.is_active is True

            # run task twice expecting same result
            for _ in range(2):
                automatic_adviser_deactivate(limit=200)

                adviser1.refresh_from_db()
                adviser2.refresh_from_db()
                adviser3.refresh_from_db()

                assert adviser1.is_active is False
                assert adviser2.is_active is False
                assert adviser3.is_active is True

    @pytest.mark.parametrize(
        'factory, adviser_attribute_name, date_attribute_name',
        (
            (InteractionDITParticipantFactory, 'adviser', 'interaction__date'),
            (EventFactory, 'organiser', 'start_date'),
            (EventFactory, 'organiser', 'end_date'),
        ),
    )
    def test_adviser_with_old_activity_but_recently_dated_object_does_not_deactivate(
            self,
            factory,
            adviser_attribute_name,
            date_attribute_name,
    ):
        """
        Test adviser with recently dated object doesn't deactivate

        Make sure that even if the changes were done a long time ago, the recently dated objects
        prevent the adviser from being deactivated
        """
        with freeze_time('2017-02-21'):
            three_years_ago = date.today() - relativedelta(years=3)
            two_years_ago = date.today() - relativedelta(years=2)

            adviser1 = deactivateable_adviser()

            adviser2 = deactivateable_adviser()
            with freeze_time(three_years_ago):
                factory(**{
                    adviser_attribute_name: adviser2,
                    date_attribute_name: two_years_ago - relativedelta(days=1),
                })

            adviser3 = deactivateable_adviser()
            with freeze_time(three_years_ago):
                factory(**{
                    adviser_attribute_name: adviser3,
                    date_attribute_name: two_years_ago,
                })

            assert adviser1.is_active is True
            assert adviser2.is_active is True
            assert adviser3.is_active is True

            # run task twice expecting same result
            for _ in range(2):
                automatic_adviser_deactivate(limit=200)

                adviser1.refresh_from_db()
                adviser2.refresh_from_db()
                adviser3.refresh_from_db()

                assert adviser1.is_active is False
                assert adviser2.is_active is False
                assert adviser3.is_active is True

    @pytest.mark.parametrize(
        'factory, attribute_name',
        (
            (OneListCoreTeamMemberFactory, 'adviser'),
            (InvestmentProjectTeamMemberFactory, 'adviser'),
        ),
    )
    def test_adviser_that_is_a_member_of_team_does_not_deactivate(
        self, factory, attribute_name,
    ):
        """
        Test adviser that is a member of a team does not deactivate, even if old
        """
        with freeze_time('2017-02-21'):
            three_years_ago = date.today() - relativedelta(years=3)

            adviser1 = deactivateable_adviser()
            adviser2 = deactivateable_adviser()
            with freeze_time(three_years_ago):
                factory(**{attribute_name: adviser2})

            assert adviser1.is_active is True
            assert adviser2.is_active is True

            # run task twice expecting same result
            for _ in range(2):
                automatic_adviser_deactivate(limit=200)

                adviser1.refresh_from_db()
                adviser2.refresh_from_db()

                assert adviser1.is_active is False
                assert adviser2.is_active is True

    def test_job_schedules_with_correct_adviser_deactivate_details(self):
        actual_job = schedule_automatic_adviser_deactivate(limit=1000, simulate=True)

        assert actual_job is not None
        assert actual_job._func_name == 'datahub.company.tasks.adviser.automatic' \
            + '_adviser_deactivate'
        assert actual_job._args == (1000, True)
        assert actual_job.retries_left == 3
        assert actual_job.origin == 'long-running'
