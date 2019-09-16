import factory
import pytest
from django.conf import settings

from datahub.company.models import OneListTier
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyCountryOfInterestFactory,
    CompanyFactory,
    ContactFactory,
    OneListCoreTeamMemberFactory,
)
from datahub.core import constants
from datahub.metadata.models import Country


# mark the whole module for db use
pytestmark = pytest.mark.django_db


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

    @pytest.mark.countries_of_interest
    def test_get_active_company_countries_of_interest_empty(self):
        """
        Test the get_active_company_countries_of_interest method when there are no
        CompanyCountryOfInterest objects at all.
        """
        company = CompanyFactory()
        assert list(company.get_active_countries_of_interest()) == []

    @pytest.mark.countries_of_interest
    def test_get_active_company_countries_of_interest_all_deleted(self):
        """
        Test the get_active_company_countries_of_interest method when all of the company's
        countries of interest are deleted.
        """
        company = CompanyFactory()
        CompanyCountryOfInterestFactory.create_batch(3, company=company, deleted=True)
        assert list(company.get_active_countries_of_interest()) == []

    @pytest.mark.countries_of_interest
    def test_get_active_company_countries_of_interest_all_for_other_companies(self):
        """
        Test the get_active_company_countries_of_interest method when all countries
        of interest are for another company.
        """
        company = CompanyFactory()
        company_2 = CompanyFactory()
        CompanyCountryOfInterestFactory.create_batch(3, company=company_2)
        assert list(company.get_active_countries_of_interest()) == []

    @pytest.mark.countries_of_interest
    def test_get_active_company_countries_of_interest_mix(self):
        """
        Test the get_active_company_countries_of_interest method when there is a mix
        of sources for the company's countries of interest. (It should have no effect
        on the output of this method.)
        """
        company = CompanyFactory()
        company_2 = CompanyFactory()
        ccoi1 = CompanyCountryOfInterestFactory(
            company=company, source='user', deleted=False,
        )
        ccoi2 = CompanyCountryOfInterestFactory(
            company=company, source='external', deleted=False,
        )
        _ = CompanyCountryOfInterestFactory(company=company_2)
        _ = CompanyCountryOfInterestFactory(company=company, deleted=True)
        CompanyCountryOfInterestFactory.create_batch(3, company=company, deleted=True)
        assert list(company.get_active_countries_of_interest()) == sorted(
            [ccoi1.country, ccoi2.country], key=lambda c: c.name,
        )

    @pytest.mark.countries_of_interest
    def test_get_active_company_countries_of_interest_non_unique(self):
        """
        If there is a user source and an external source for the same country,
        the country should only be returned once
        """
        company = CompanyFactory()
        ccoi1 = CompanyCountryOfInterestFactory(
            company=company, source='user', deleted=False,
        )
        CompanyCountryOfInterestFactory(
            company=company, country=ccoi1.country, source='external', deleted=False,
        )
        assert list(company.get_active_countries_of_interest()) == [ccoi1.country]

    @pytest.mark.countries_of_interest
    def test_set_user_edited_countries_of_interest_all_new(self):
        """
        Test the set_user_edited_countries_of_interest method with a list
        of all new countries.
        """
        company_1 = CompanyFactory()
        company_2 = CompanyFactory()
        _ = CompanyCountryOfInterestFactory(company=company_2)
        countries = Country.objects.all()[:2]
        company_1.set_user_edited_countries_of_interest([countries[0], countries[1]])
        assert (
            list(company_1.raw_countries_of_interest.values_list('country', 'source', 'deleted'))
            == [(countries[0].id, 'user', False), (countries[1].id, 'user', False)]
        )

    @pytest.mark.countries_of_interest
    def test_set_user_edited_countries_of_interest_including_existing_external(self):
        """
        If we already had an externally sourced country of interest that was not deleted,
        then saving that country again by the user shouldn't change its source to user.
        """
        company_1 = CompanyFactory()
        c1 = CompanyCountryOfInterestFactory(company=company_1, source='external', deleted=False)
        company_1.set_user_edited_countries_of_interest([c1.country])
        assert (
            list(company_1.raw_countries_of_interest.values_list('country', 'source', 'deleted'))
            == [(c1.country.id, 'external', False)]
        )

    @pytest.mark.countries_of_interest
    def test_set_user_edited_countries_of_interest_including_existing_deleted_external(self):
        """
        If we  had an externally sourced country of interest that *was* deleted,
        then that has to be un-deleted, plus the user-sourced country has to be added
        as well.
        """
        company_1 = CompanyFactory()
        c1 = CompanyCountryOfInterestFactory(company=company_1, source='external', deleted=True)
        company_1.set_user_edited_countries_of_interest([c1.country])
        assert (
            list(company_1.raw_countries_of_interest.values_list('country', 'source', 'deleted'))
            == [(c1.country.id, 'external', True), (c1.country.id, 'user', False)]
        )

    @pytest.mark.countries_of_interest
    def test_set_user_edited_countries_of_interest_all_existing_some_deleted(self):
        """
        Test the set_user_edited_countries_of_interest method, if the input we supply
        only contains countries of interest that already exist, albeit some of them
        deleted
        """
        company_1 = CompanyFactory()
        company_2 = CompanyFactory()
        _ = CompanyCountryOfInterestFactory(company=company_2)
        c1 = CompanyCountryOfInterestFactory(
            company=company_1, source='user',
        )
        c2 = CompanyCountryOfInterestFactory(
            company=company_1, source='user', deleted=True,
        )
        company_1.set_user_edited_countries_of_interest([c1.country, c2.country])
        assert (
            sorted(list(
                company_1.raw_countries_of_interest.values_list('country', 'source', 'deleted'),
            ))
            == sorted([(c1.country.id, 'user', False), (c2.country.id, 'user', False)])
        )

    @pytest.mark.countries_of_interest
    def test_set_user_edited_countries_of_interest_some_removed_some_added(self):
        """
        Test the set_user_edited_countries_of_interest method, if we supply input
        that represents the removal of some countries of interest and the addition of others.
        """
        company_1 = CompanyFactory()
        company_2 = CompanyFactory()
        CompanyCountryOfInterestFactory.create_batch(3, company=company_2)
        c1 = CompanyCountryOfInterestFactory(
            company=company_1, source='user',
        )
        c2 = CompanyCountryOfInterestFactory(
            company=company_1, source='user', deleted=True,
        )
        # We'll remove c3
        c3 = CompanyCountryOfInterestFactory(
            company=company_1, source='external',
        )
        c4 = CompanyCountryOfInterestFactory(
            company=company_1, source='external', deleted=True,
        )

        other_country = Country.objects.exclude(id__in=[c1.id, c2.id, c3.id, c4.id]).first()
        company_1.set_user_edited_countries_of_interest([
            c1.country, c2.country, c4.country, other_country,
        ])

        assert (
            sorted(list(
                company_1.raw_countries_of_interest.values_list('country', 'source', 'deleted'),
            ))
            == sorted([
                (c1.country_id, 'user', False),
                (c2.country_id, 'user', False),
                (c3.country_id, 'external', True),
                (c4.country_id, 'external', True),
                (c4.country_id, 'user', False),
                (other_country.id, 'user', False),
            ])
        )

    @pytest.mark.countries_of_interest
    def test_set_user_edited_countries_of_interest_all_removed(self):
        """
        Test the set_user_edited_countries_of_interest method if we remove all
        countries of interest
        """
        company_1 = CompanyFactory()
        company_2 = CompanyFactory()
        CompanyCountryOfInterestFactory.create_batch(3, company=company_2)
        c1 = CompanyCountryOfInterestFactory(
            company=company_1, source='user',
        )
        c2 = CompanyCountryOfInterestFactory(
            company=company_1, source='user', deleted=True,
        )
        c3 = CompanyCountryOfInterestFactory(
            company=company_1, source='external',
        )
        c4 = CompanyCountryOfInterestFactory(
            company=company_1, source='external', deleted=True,
        )
        company_1.set_user_edited_countries_of_interest([])
        assert (
            sorted(list(
                company_1.raw_countries_of_interest.values_list('country', 'source', 'deleted'),
            ))
            == sorted([
                (c1.country_id, 'user', True),
                (c2.country_id, 'user', True),
                (c3.country_id, 'external', True),
                (c4.country_id, 'external', True),
            ])
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


@pytest.mark.countries_of_interest
class TestCompanyCountryOfInterest:
    """Tests for the CompanyCountryOfInterest model."""

    def test_str(self):
        """Test the human-friendly string representation of a CompanyCountryOfInterest object."""
        company = CompanyFactory(name='Acme Corp.')
        ccoi = CompanyCountryOfInterestFactory.build(
            country=Country.objects.get(id=constants.Country.anguilla.value.id),
            company=company,
            source='user',
            deleted=False,
        )
        assert str(ccoi) == (
            '<CompanyCountryOfInterest: Acme Corp. interested in Anguilla; '
            'Source: user; Deleted: False>'
        )
