import uuid
from contextlib import contextmanager
from io import StringIO
from operator import attrgetter
from unittest import mock

import pytest
from botocore.exceptions import ClientError
from django.core.management import call_command

from datahub.company.management.commands.import_export_countries import (
    import_from_csv,
    InvalidImportDataError,
    update_missing_companies,
)
from datahub.company.models import Company, CompanyExportCountry
from datahub.company.test.factories import CompanyExportCountryFactory, CompanyFactory
from datahub.metadata.models import Country


mock_company_path = (
    'datahub.company.management.commands.import_export_countries.Company'
)
EXTERNAL_SOURCE = CompanyExportCountry.SOURCES.external
USER_SOURCE = CompanyExportCountry.SOURCES.user


@pytest.fixture
def mock_company_class(company_1, company_2):
    """
    Mock the company class to return a particular mock object as the result
    of any .objects.get call.
    """
    def get_company(id):
        if str(company_1.id) == id:
            return company_1
        elif str(company_2.id) == id:
            return company_2
        else:
            raise Company.DoesNotExist()

    with mock.patch.object(Company.objects, 'get', side_effect=get_company):
        yield


@pytest.fixture
def company_1(db):
    """
    Create a company with the set_external_source_export_countries
    method mock.patched. This will also be used in the mock_company_class
    fixture.
    """
    company_1 = CompanyFactory()
    with mock.patch.object(
        company_1, 'set_external_source_export_countries',
    ):
        yield company_1


@pytest.fixture
def company_2(company_1):
    """
    Create a company with the set_external_source_export_countries
    method mock.patched. This will also be used in the mock_company_class
    fixture.
    """
    company_2 = CompanyFactory()
    while str(company_2.id) <= str(company_1.id):
        company_2 = CompanyFactory()
    with mock.patch.object(
        company_2, 'set_external_source_export_countries',
    ):
        yield company_2


def mock_file_contents_with(data):
    """
    Given a list of (company, country) tuples, patch the open_s3_file
    function so that it returns a file-like object with the expected
    text lines representing that data.
    """
    text_lines = [
        f'{company.id},{country.name},{country.iso_alpha2_code}'
        for (company, country)
        in data
    ]
    return mock_file_contents(text_lines)


@contextmanager
def mock_file_contents(text_lines):
    """
    Given a list of strings, patch the open_s3_file
    function so that it returns a file-like object with these strings
    as its lines.
    """
    with mock.patch(
        'datahub.company.management.commands.import_export_countries.open_s3_file',
    ) as mocked_open_s3:
        mocked_open_s3.return_value.__enter__.side_effect = lambda: iter(text_lines)
        yield mocked_open_s3


def check_call_args(company, arg):
    """
    Check the call args list of the given company's set_external_source_export_countries
    method. This check only supports checking a single call, with a single arg,
    so we assert that the length of the method's call_args is 1, and that the lengths
    of the args for that call is 1.
    """
    call_args = company.set_external_source_export_countries.call_args_list
    assert len(call_args) == 1
    assert len(call_args[0][0]) == 1
    # The first 0 index gets the first time the method was called.
    # The second 0 index gets args as opposed to kwargs.
    # The third 0 index gets the first arg of this call.
    # Then assert that this arg is equal to the supplied arg.
    assert call_args[0][0][0] == arg


@pytest.mark.external_export_countries
def test_import_export_countries_command():
    """
    Test the command itself, that it calls the inner function
    with the supplied filename as an argument
    """
    out = StringIO()
    with mock.patch(
        'datahub.company.management.commands.import_export_countries.import_from_csv',
    ) as mocked:
        call_command('import_export_countries', 'bucket', 'key', stdout=out)
    assert mocked.called_once_with('bucket', 'key')


@pytest.mark.external_export_countries
@pytest.mark.export_countries
@pytest.mark.django_db
class TestImportCountriesOfInterest:
    """
    Tests covering the import_from_csv function in the
    import_export_countries commmand module
    """

    def test_unsorted(self, company_1, company_2):
        """
        Test that if input csv is not sorted by company, an error will be raised
        """
        country_1 = Country.objects.first()
        test_data = [
            (company_1, country_1),
            (company_2, country_1),
            (company_1, country_1),
        ]
        with mock_file_contents_with(test_data):
            with pytest.raises(InvalidImportDataError):
                import_from_csv('', '')

    def test_non_existent_country(self):
        """Test that non-existent country raises error"""
        company_1 = CompanyFactory()
        text_lines = [f'{company_1.id},Name,ZZ']
        with mock_file_contents(text_lines):
            with pytest.raises(InvalidImportDataError):
                import_from_csv('', '')

    def test_file_missing(self):
        """Test that missing file doesn't do anything"""
        cec = CompanyExportCountryFactory(sources=[EXTERNAL_SOURCE])
        with mock.patch(
            'datahub.company.management.commands.import_export_countries.open_s3_file',
        ) as mocked_open_s3:
            error_response = {
                'Error': {
                    'Code': 'NoSuchKey', 'Message': 'The specified key does not exist.',
                },
            }
            mocked_open_s3.return_value.__enter__.side_effect = ClientError(
                error_response,
                'GetObject',
            )
            with pytest.raises(ClientError):
                import_from_csv('', '')

        try:
            # Should be no error
            cec.refresh_from_db()
        except CompanyExportCountry.DoesNotExist:
            pytest.fail('CompanyExportCountry seems to have been deleted unexpectedly')

    def test_empty_file(self):
        """Test that empty file deletes everything"""
        CompanyExportCountryFactory.create_batch(4, sources=[EXTERNAL_SOURCE])
        assert CompanyExportCountry.objects.filter(deleted=False).count() == 4  # Test the test
        with mock_file_contents([]):
            import_from_csv('', '')

        # Have to check this in a more integrationy way because it is difficult
        # to patch the Company objects within update_missing_companies.
        assert CompanyExportCountry.objects.filter(deleted=False).count() == 0

    def test_one_company_one_country(self, mock_company_class, company_1):
        """Test if there is one company with one country in the file"""
        country_1 = Country.objects.first()
        with mock_file_contents_with([(company_1, country_1)]):
            import_from_csv('', '')
        check_call_args(company_1, [country_1])

    def test_non_existent_company(self, mock_company_class, company_1):
        """Non existing company will just be skipped"""
        country_1 = Country.objects.first()
        test_text = [
            f'{uuid.uuid4()},{country_1.name},{country_1.iso_alpha2_code}',
            f'{company_1.id},{country_1.name},{country_1.iso_alpha2_code}',
        ]
        test_text = sorted(test_text)
        with mock_file_contents(test_text):
            import_from_csv('', '')
        check_call_args(company_1, [country_1])

    def test_one_company_two_countries(self, mock_company_class, company_1):
        """Test if there is one company with two countries in the file"""
        countries = Country.objects.all()[:2]
        test_data = [
            (company_1, countries[0]),
            (company_1, countries[1]),
        ]
        with mock_file_contents_with(test_data):
            import_from_csv('', '')
        check_call_args(company_1, [countries[0], countries[1]])

    def test_two_companies_one_country(self, mock_company_class, company_1, company_2):
        """Test if there are two companies in the file, each with one country"""
        countries = Country.objects.all()[:2]
        test_data = [
            (company_1, countries[0]),
            (company_2, countries[1]),
        ]
        with mock_file_contents_with(test_data):
            import_from_csv('', '')
        check_call_args(company_1, [countries[0]])
        check_call_args(company_2, [countries[1]])

    def test_two_companies_two_countries(self, mock_company_class, company_1, company_2):
        """Test if there are two companies in the file, each with two countries"""
        countries = Country.objects.all()[:4]
        test_data = [
            (company_1, countries[0]),
            (company_1, countries[1]),
            (company_2, countries[2]),
            (company_2, countries[3]),
        ]
        with mock_file_contents_with(test_data):
            import_from_csv('', '')
        check_call_args(company_1, [countries[0], countries[1]])
        check_call_args(company_2, [countries[2], countries[3]])

    def test_company_missing(self, mock_company_class, company_1, company_2):
        """
        Test that if a company has a CompanyExportCountry, but
        the company does not appear in the import, it will be deleted.
        """
        cec1 = CompanyExportCountryFactory(
            company=company_1,
            sources=[USER_SOURCE],
        )
        cec2 = CompanyExportCountryFactory(
            company=company_2,
            sources=[EXTERNAL_SOURCE],
        )
        with mock_file_contents([]):
            import_from_csv('', '')
        # Have to check this in a more integrationy way because it is difficult
        # to patch the Company objects within update_missing_companies.
        cec1.refresh_from_db()
        assert cec1.deleted is False
        with pytest.raises(CompanyExportCountry.DoesNotExist):
            cec2.refresh_from_db()


@pytest.mark.external_export_countries
@pytest.mark.export_countries
@pytest.mark.django_db
class TestUpdateMissingCompanies:
    """Test the update_missing_companies function"""

    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def one_time_setup(self, request, django_db_setup, django_db_blocker):  # noqa: N804
        """
        All tests in this class will use the same basic datasetup:
        12 Companies, each with one user-source export country and one external-source
        export country.
        By using this slightly complicated one_time_setup, class-scoped fixture thingy,
        we can speed up these tests considerably.
        There is a function scoped fixture below, called 'setup', which just needs
        to quickly reset all CompanyExportCountrys' 'deleted' fields to False,
        as the individual tests in this class only modify that field.
        """
        cls = type(self)
        django_db_blocker.unblock()
        request.addfinalizer(django_db_blocker.restore)
        from django.test import TestCase
        test_case = TestCase(methodName='__init__')
        test_case._pre_setup()
        request.addfinalizer(test_case._post_teardown)

        cls.companies = CompanyFactory.create_batch(12)
        cls.companies = sorted(cls.companies, key=attrgetter('id'))
        cls.external_cecs = []
        cls.user_cecs = []
        for company in cls.companies:
            cls.external_cecs.append(
                CompanyExportCountryFactory(
                    company=company,
                    sources=[EXTERNAL_SOURCE],
                    deleted=False,
                ),
            )
            cls.user_cecs.append(
                CompanyExportCountryFactory(
                    company=company,
                    sources=[USER_SOURCE],
                    deleted=False,
                ),
            )

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Reset deleted=False for all CompanyExportCountry, because these objects
        are not recreated with each test, because of the way we have done one_time_setup
        fixture above.
        """
        CompanyExportCountry.objects.update(deleted=False)

    def test_empty_file(self):
        """
        Test that we can handle an empty file.
        """
        with mock_file_contents([]):
            update_missing_companies('', '')
        all_user_cecs = CompanyExportCountry.objects.filter(sources=[USER_SOURCE])
        all_external_cecs = CompanyExportCountry.objects.filter(sources=[EXTERNAL_SOURCE])

        # All of these deleted
        assert all_external_cecs.count() == 0
        # None of these deleted
        assert all_user_cecs.filter(deleted=False).count() == len(self.user_cecs)

    @pytest.mark.parametrize('batch_size', [20, 3, 2])
    @pytest.mark.parametrize('missing_first_third', [True, False])
    @pytest.mark.parametrize('missing_last_third', [True, False])
    @pytest.mark.parametrize('missing_1_mod_3', [True, False])
    def test_companies_missing(
        self, batch_size, missing_first_third, missing_last_third, missing_1_mod_3,
    ):
        """
        Test combinations of:
            sequence missing at start of range,
            sequence missing at end of range,
            every third company missing,
            different batch sizes (which cause different code paths to get excercised)
        """
        present_companies = self.companies
        # Adequate coverage relies on a certain number of companies present
        assert len(present_companies) == 12

        if missing_first_third:
            present_companies = present_companies[4:]
        if missing_last_third:
            present_companies = present_companies[:-4]
        if missing_1_mod_3:
            present_companies = [
                company
                for i, company in enumerate(present_companies)
                if i % 3 != 1
            ]

        test_data = [
            (company, company.unfiltered_export_countries.filter(
                sources=[EXTERNAL_SOURCE],
            ).first().country)
            for company in present_companies
        ]
        with mock_file_contents_with(test_data):
            with mock.patch(
                'datahub.company.management.commands.import_export_countries.COMPANY_BATCH_SIZE',
                batch_size,
            ):
                update_missing_companies('', '')

        expected_deleted_cecs = CompanyExportCountry.objects.filter(
            sources=[EXTERNAL_SOURCE],
        ).exclude(
            company__in=present_companies,
        )
        expected_active_cecs = CompanyExportCountry.objects.filter(
            sources=[EXTERNAL_SOURCE],
            company__in=present_companies,
        )
        # All of these deleted
        assert set(CompanyExportCountry.objects.filter(
            sources=[EXTERNAL_SOURCE],
            deleted=True,
        ).values_list('id', flat=True)) == set(cec.id for cec in expected_deleted_cecs)

        assert set(CompanyExportCountry.objects.filter(
            sources=[EXTERNAL_SOURCE],
            deleted=False,
        ).values_list('id', flat=True)) == set(cec.id for cec in expected_active_cecs)

        # None of these deleted
        assert CompanyExportCountry.objects.filter(
            sources=[USER_SOURCE],
            deleted=False,
        ).count() == len(self.user_cecs)
