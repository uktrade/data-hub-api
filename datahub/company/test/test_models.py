from copy import copy
from datetime import timedelta

import factory
import pytest
from django.conf import settings
from django.utils import timezone as tz

from datahub.company.models import Company, CompanyExportCountry, OneListTier
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyExportCountryFactory,
    CompanyFactory,
    ContactFactory,
    OneListCoreTeamMemberFactory,
)
from datahub.core import constants
from datahub.metadata.models import Country


# mark the whole module for db use
pytestmark = pytest.mark.django_db


EXTERNAL_SOURCE = CompanyExportCountry.SOURCES.external
USER_SOURCE = CompanyExportCountry.SOURCES.user


class TestCompany:
    """Tests for the company model."""

    def test_get_absolute_url(self):
        """Test that Company.get_absolute_url() returns the correct URL."""
        company = CompanyFactory.build()
        assert company.get_absolute_url() == (
            f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["company"]}/{company.pk}'
        )

    @pytest.mark.parametrize(
        'build_global_headquarters',
        (
            lambda: CompanyFactory.build(),
            lambda: None,
        ),
        ids=('as_subsidiary', 'as_non_subsidiary'),
    )
    def test_get_group_global_headquarters(self, build_global_headquarters):
        """
        Test that `get_group_global_headquarters` returns `self` if the company has
        no `global_headquarters` or the `global_headquarters` otherwise.
        """
        company = CompanyFactory.build(
            global_headquarters=build_global_headquarters(),
        )

        expected_group_global_headquarters = company.global_headquarters or company
        assert company.get_group_global_headquarters() == expected_group_global_headquarters

    @pytest.mark.parametrize(
        'build_company',
        (
            # subsidiary with Global Headquarters on the One List
            lambda one_list_tier: CompanyFactory(
                one_list_tier=None,
                global_headquarters=CompanyFactory(one_list_tier=one_list_tier),
            ),
            # subsidiary with Global Headquarters not on the One List
            lambda one_list_tier: CompanyFactory(
                one_list_tier=None,
                global_headquarters=CompanyFactory(one_list_tier=None),
            ),
            # single company on the One List
            lambda one_list_tier: CompanyFactory(
                one_list_tier=one_list_tier,
                global_headquarters=None,
            ),
            # single company not on the One List
            lambda one_list_tier: CompanyFactory(
                one_list_tier=None,
                global_headquarters=None,
            ),
        ),
        ids=(
            'as_subsidiary_of_one_list_company',
            'as_subsidiary_of_non_one_list_company',
            'as_one_list_company',
            'as_non_one_list_company',
        ),
    )
    def test_get_one_list_group_tier(self, build_company):
        """
        Test that `get_one_list_group_tier` returns the One List Tier of `self`
        if company has no `global_headquarters` or the one of its `global_headquarters`
        otherwise.
        """
        one_list_tier = OneListTier.objects.first()

        company = build_company(one_list_tier)

        group_global_headquarters = company.global_headquarters or company
        if not group_global_headquarters.one_list_tier:
            assert not company.get_one_list_group_tier()
        else:
            assert company.get_one_list_group_tier() == one_list_tier

    @pytest.mark.parametrize(
        'build_company',
        (
            # as subsidiary
            lambda gam: CompanyFactory(
                global_headquarters=CompanyFactory(one_list_account_owner=gam),
            ),
            # as single company
            lambda gam: CompanyFactory(
                global_headquarters=None,
                one_list_account_owner=gam,
            ),
        ),
        ids=('as_subsidiary', 'as_non_subsidiary'),
    )
    @pytest.mark.parametrize(
        'with_global_account_manager',
        (True, False),
        ids=lambda val: f'{"With" if val else "Without"} global account manager',
    )
    def test_get_one_list_group_core_team(
        self,
        build_company,
        with_global_account_manager,
    ):
        """
        Test that `get_one_list_group_core_team` returns the Core Team of `self` if the company
        has no `global_headquarters` or the one of its `global_headquarters` otherwise.
        """
        team_member_advisers = AdviserFactory.create_batch(
            3,
            first_name=factory.Iterator(
                ('Adam', 'Barbara', 'Chris'),
            ),
        )
        global_account_manager = team_member_advisers[0] if with_global_account_manager else None

        company = build_company(global_account_manager)
        group_global_headquarters = company.global_headquarters or company

        OneListCoreTeamMemberFactory.create_batch(
            len(team_member_advisers),
            company=group_global_headquarters,
            adviser=factory.Iterator(team_member_advisers),
        )

        core_team = company.get_one_list_group_core_team()
        assert core_team == [
            {
                'adviser': adviser,
                'is_global_account_manager': adviser is global_account_manager,
            }
            for adviser in team_member_advisers
        ]

    @pytest.mark.parametrize(
        'build_company',
        (
            # subsidiary with Global Headquarters on the One List
            lambda one_list_tier, gam: CompanyFactory(
                one_list_tier=None,
                global_headquarters=CompanyFactory(
                    one_list_tier=one_list_tier,
                    one_list_account_owner=gam,
                ),
            ),
            # subsidiary with Global Headquarters not on the One List
            lambda one_list_tier, gam: CompanyFactory(
                one_list_tier=None,
                global_headquarters=CompanyFactory(
                    one_list_tier=None,
                    one_list_account_owner=None,
                ),
            ),
            # single company on the One List
            lambda one_list_tier, gam: CompanyFactory(
                one_list_tier=one_list_tier,
                one_list_account_owner=gam,
                global_headquarters=None,
            ),
            # single company not on the One List
            lambda one_list_tier, gam: CompanyFactory(
                one_list_tier=None,
                global_headquarters=None,
                one_list_account_owner=None,
            ),
        ),
        ids=(
            'as_subsidiary_of_one_list_company',
            'as_subsidiary_of_non_one_list_company',
            'as_one_list_company',
            'as_non_one_list_company',
        ),
    )
    def test_get_one_list_group_global_account_manager(self, build_company):
        """
        Test that `get_one_list_group_global_account_manager` returns
        the One List Global Account Manager of `self` if the company has no
        `global_headquarters` or the one of its `global_headquarters` otherwise.
        """
        global_account_manager = AdviserFactory()
        one_list_tier = OneListTier.objects.first()

        company = build_company(one_list_tier, global_account_manager)

        group_global_headquarters = company.global_headquarters or company
        actual_global_account_manager = company.get_one_list_group_global_account_manager()
        assert group_global_headquarters.one_list_account_owner == actual_global_account_manager

    @pytest.mark.export_countries
    def test_get_active_company_export_countries_empty(self):
        """
        Test the get_active_company_export_countries method when there are no
        CompanyExportCountry objects at all.
        """
        company = CompanyFactory()
        assert list(company.get_active_future_export_countries()) == []

    @pytest.mark.export_countries
    def test_get_active_company_export_countries_all_disabled(self):
        """
        Test the get_active_company_export_countries method when all of the company's
        countries of interest are disabled.
        """
        company = CompanyFactory()
        CompanyExportCountryFactory.create_batch(3, company=company, disabled=True)
        assert list(company.get_active_future_export_countries()) == []

    @pytest.mark.export_countries
    def test_get_active_company_export_countries_all_for_other_companies(self):
        """
        Test the get_active_company_export_countries method when all countries
        of interest are for another company.
        """
        company = CompanyFactory()
        company_2 = CompanyFactory()
        CompanyExportCountryFactory.create_batch(3, company=company_2)
        assert list(company.get_active_future_export_countries()) == []

    @pytest.mark.export_countries
    @pytest.mark.parametrize('prefetch', [True, False, 'partial'])
    def test_get_active_company_export_countries_mix(self, prefetch):
        """
        Test the get_active_company_export_countries method when there is a mix
        of sources for the company's countries of interest. (It should have no effect
        on the output of this method.)
        """
        company = CompanyFactory()
        company_2 = CompanyFactory()
        cec1 = CompanyExportCountryFactory(
            company=company, sources=[USER_SOURCE], disabled=False,
        )
        cec2 = CompanyExportCountryFactory(
            company=company, sources=[EXTERNAL_SOURCE], disabled=False,
        )
        cec3 = CompanyExportCountryFactory(
            company=company, sources=[USER_SOURCE, EXTERNAL_SOURCE], disabled=False,
        )
        _ = CompanyExportCountryFactory(company=company_2)
        _ = CompanyExportCountryFactory(company=company, disabled=True)
        CompanyExportCountryFactory.create_batch(3, company=company, disabled=True)

        companies = Company.objects.filter(id=company.id)
        # Should work regardless of prefetches
        if prefetch:
            companies = companies.prefetch_related('unfiltered_export_countries')
            if prefetch is True:
                companies = companies.prefetch_related('unfiltered_export_countries__country')

        assert list(companies[0].get_active_future_export_countries()) == sorted(
            [cec1.country, cec2.country, cec3.country], key=lambda c: c.name,
        )


class TestContact:
    """Tests for the contact model."""

    def test_get_absolute_url(self):
        """Test that Contact.get_absolute_url() returns the correct URL."""
        contact = ContactFactory.build()
        assert contact.get_absolute_url() == (
            f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["contact"]}/{contact.pk}'
        )

    @pytest.mark.parametrize(
        'first_name,last_name,company_factory,expected_output',
        (
            ('First', 'Last', lambda: CompanyFactory(name='Company'), 'First Last (Company)'),
            ('', 'Last', lambda: CompanyFactory(name='Company'), 'Last (Company)'),
            ('First', '', lambda: CompanyFactory(name='Company'), 'First (Company)'),
            ('First', 'Last', lambda: None, 'First Last'),
            ('First', 'Last', lambda: CompanyFactory(name=''), 'First Last'),
            ('', '', lambda: CompanyFactory(name='Company'), '(no name) (Company)'),
            ('', '', lambda: None, '(no name)'),
        ),
    )
    def test_str(self, first_name, last_name, company_factory, expected_output):
        """Test the human-friendly string representation of a Contact object."""
        contact = ContactFactory.build(
            first_name=first_name,
            last_name=last_name,
            company=company_factory(),
        )
        assert str(contact) == expected_output


@pytest.mark.export_countries
class TestCompanyExportCountry:
    """Tests for the CompanyExportCountry model."""

    def test_str(self):
        """Test the human-friendly string representation of a CompanyExportCountry object."""
        company = CompanyFactory(name='Acme Corp.')
        cec = CompanyExportCountryFactory.build(
            country=Country.objects.get(id=constants.Country.anguilla.value.id),
            company=company,
            sources=[USER_SOURCE],
            disabled=False,
        )
        assert str(cec) == (
            """Acme Corp. interested in Anguilla; Sources: ['user']; Disabled: False"""
        )

    def test_enable_no_user(self):
        """Test the enable method called with no user argument"""
        user = AdviserFactory()
        cec = CompanyExportCountryFactory.build(disabled=True, disabled_by=user)
        cec.enable()
        assert cec.disabled_on is None
        assert cec.disabled_by is None
        assert cec.modified_by is None

    def test_enable_by_user(self):
        """Test the enable method called with a user argument"""
        user = AdviserFactory()
        cec = CompanyExportCountryFactory.build(disabled=True, disabled_by=user)
        cec.enable(user)
        assert cec.disabled_on is None
        assert cec.disabled_by is None
        assert cec.modified_by == user

    def test_disable_no_user(self):
        """Test the disable method called with no user argument"""
        cec = CompanyExportCountryFactory.build()
        cec.disable()
        assert cec.disabled_on is not None
        assert cec.disabled_by is None
        assert cec.modified_by is None

    def test_disable_by_user(self):
        """Test the disable method called with a user argument"""
        user = AdviserFactory()
        cec = CompanyExportCountryFactory.build()
        cec.disable(user)
        assert cec.disabled_on is not None
        assert cec.disabled_by == user
        assert cec.modified_by == user

    @pytest.mark.parametrize('existing_sources', [
        [],
        [USER_SOURCE],
        [EXTERNAL_SOURCE],
        [USER_SOURCE, EXTERNAL_SOURCE],
        [EXTERNAL_SOURCE, USER_SOURCE],
    ])
    @pytest.mark.parametrize('new_source', [
        USER_SOURCE,
        EXTERNAL_SOURCE,
    ])
    @pytest.mark.parametrize('disabled,disabled_by_user,source_time_later', [
        [False, False, False],
        [True, False, False],
        [True, False, True],
        [True, True, False],
        [True, True, True],
    ])
    def test_add_source(
        self, existing_sources, new_source, disabled, disabled_by_user, source_time_later,
    ):
        """Test the add_source method in a variety of circumstances"""
        cec = CompanyExportCountryFactory(
            sources=copy(existing_sources),
            disabled=disabled,
            disabled_by=AdviserFactory() if disabled_by_user else None,
        )
        source_time = cec.disabled_on
        if source_time_later:
            source_time += timedelta(microseconds=1)
        user = AdviserFactory() if new_source == USER_SOURCE else None

        cec.add_source(new_source, source_time, user=user)
        cec.refresh_from_db()
        if new_source not in existing_sources:
            assert cec.sources == existing_sources + [new_source]
        else:
            assert cec.sources == existing_sources
        if disabled and (user or not disabled_by_user or source_time_later):
            assert cec.disabled_on is None
            assert cec.disabled_by is None
            assert cec.modified_by == user
        else:
            if disabled:
                assert cec.disabled_on is not None
            else:
                assert cec.disabled_on is None

            if disabled_by_user:
                assert cec.disabled_by is not None
            else:
                assert cec.disabled_by is None

    def test_add_user_source_user_required(self):
        """
        Test that the user argument is required for the add_source method when the source
        you are adding is the user source.
        """
        cec = CompanyExportCountryFactory.build()
        with pytest.raises(ValueError):
            cec.add_source(CompanyExportCountry.SOURCES.user, tz.now())

    @pytest.mark.parametrize('existing_sources', [
        [],
        [USER_SOURCE],
        [EXTERNAL_SOURCE],
        [USER_SOURCE, EXTERNAL_SOURCE],
        [EXTERNAL_SOURCE, USER_SOURCE],
    ])
    @pytest.mark.parametrize('remove_source', [
        USER_SOURCE,
        EXTERNAL_SOURCE,
    ])
    @pytest.mark.parametrize('disabled,disabled_by_user', [
        [False, False],
        [True, False],
        [True, True],
    ])
    def test_remove_source(
        self, existing_sources, remove_source, disabled, disabled_by_user,
    ):
        """Test the remove_source method in a variety of circumstances"""
        cec = CompanyExportCountryFactory(
            sources=copy(existing_sources),
            disabled=disabled,
            disabled_by=AdviserFactory() if disabled_by_user else None,
        )
        user = AdviserFactory() if remove_source == USER_SOURCE else None
        expected_sources = copy(existing_sources)
        if remove_source in expected_sources:
            expected_sources.remove(remove_source)
        cec.remove_source(remove_source, user=user)
        cec.refresh_from_db()
        assert cec.sources == expected_sources
        if not disabled and (user or expected_sources == []):
            assert cec.disabled_on is not None
            assert cec.disabled_by == user
            assert cec.modified_by == user
        else:
            if disabled:
                assert cec.disabled_on is not None
            else:
                assert cec.disabled_on is None
            if disabled_by_user:
                assert cec.disabled_by is not None
            else:
                assert cec.disabled_by is None

    def test_remove_user_source_user_required(self):
        """
        Test that the user argument is required for the remove_source method when the source
        you are removing is the user source.
        """
        cec = CompanyExportCountryFactory.build()
        with pytest.raises(ValueError):
            cec.remove_source(CompanyExportCountry.SOURCES.user)
