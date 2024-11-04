import gzip
import json
import logging

import boto3
import pytest

from moto import mock_aws
from sentry_sdk import init
from sentry_sdk.transport import Transport

from datahub.company.models.company import Company
from datahub.company.models.contact import Contact
from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.company_activity.models import GreatExportEnquiry, IngestedFile
from datahub.company_activity.tasks.constants import BUCKET, GREAT_PREFIX, REGION
from datahub.company_activity.tasks.ingest_great_data import (
    GreatIngestionTask, ingest_great_data,
)
from datahub.company_activity.tests.factories import (
    CompanyActivityGreatExportEnquiryFactory,
)
from datahub.metadata.models import BusinessType, Country, EmployeeRange, Sector


@pytest.fixture
def test_file():
    filepath = 'datahub/company_activity/tests/test_tasks/fixtures/great/20241023T000346.jsonl.gz'
    return open(filepath, 'rb')


@pytest.fixture
def test_file_path():
    return f'{GREAT_PREFIX}20240920T000000.jsonl.gz'


@mock_aws
def setup_s3_client():
    return boto3.client('s3', REGION)


@mock_aws
def setup_s3_bucket(bucket_name):
    mock_s3_client = setup_s3_client()
    mock_s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': REGION},
    )


@mock_aws
def setup_s3_files(bucket_name, test_file, test_file_path):
    mock_s3_client = setup_s3_client()
    mock_s3_client.put_object(Bucket=bucket_name, Key=test_file_path, Body=test_file)


class MockSentryTransport(Transport):
    def __init__(self):
        self.events = []

    def capture_event(self, event):
        pass

    def capture_envelope(self, envelope):
        self.events.append(envelope)


class TestGreatIngestionTasks:
    @pytest.mark.django_db
    @mock_aws
    def test_great_data_file_ingestion(self, caplog, test_file, test_file_path):
        """
        Test that a Great data file is ingested correctly and the ingested file
        is added to the IngestedFile table
        """
        initial_great_activity_count = GreatExportEnquiry.objects.count()
        initial_ingested_count = IngestedFile.objects.count()
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        with caplog.at_level(logging.INFO):
            ingest_great_data(BUCKET, test_file_path)
            assert f'Ingesting file: {test_file_path} started' in caplog.text
            assert f'Ingesting file: {test_file_path} finished' in caplog.text
        assert GreatExportEnquiry.objects.count() == initial_great_activity_count + 7
        assert IngestedFile.objects.count() == initial_ingested_count + 1

    @pytest.mark.django_db
    @mock_aws
    def test_skip_previously_ingested_records(self, test_file_path):
        """
        Test that we skip updating records that have already been ingested
        """
        CompanyActivityGreatExportEnquiryFactory(form_id=5249)
        record = json.dumps(dict({
            'id': '5249',
            'created_at': '2024-09-19T14:00:34.069',
        }), default=str)
        test_file = gzip.compress(record.encode('utf-8'))
        setup_s3_bucket(BUCKET)
        setup_s3_files(BUCKET, test_file, test_file_path)
        ingest_great_data(BUCKET, test_file_path)
        assert GreatExportEnquiry.objects.filter(form_id=5249).count() == 1

    @pytest.mark.django_db
    @mock_aws
    def test_invalid_file(self, test_file_path):
        """
        Test that an exception is raised when the file is not valid
        """
        mock_transport = MockSentryTransport()
        init(transport=mock_transport)
        setup_s3_bucket(BUCKET)
        with pytest.raises(Exception) as e:
            ingest_great_data(BUCKET, test_file_path)
        exception = e.value.args[0]
        assert 'The specified key does not exist' in exception
        expected = " key: 'data-flow/exports/ExportGreatContactFormData/" \
            '20240920T000000.jsonl.gz'
        assert expected in exception

    @pytest.mark.django_db
    def test_company_house_number_mapping(self):
        """
        Test that Company is mapped correctly based on Company House number if
        supplied
        """
        company = CompanyFactory(company_number='123')
        data = f"""
            {{
                "id": "5249",
                "created_at": "2024-09-19T14:00:34.069",
                "data": {{
                    "company_registration_number": "{company.company_number}"
                }}
            }}
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        result = GreatExportEnquiry.objects.get(form_id='5249')
        assert result.company.name == company.name

    @pytest.mark.django_db
    def test_company_name_mapping(self):
        """
        Test that Company is mapped correctly based on Company name if no
        number is supplied or matched
        """
        company = CompanyFactory(company_number='123')
        data = f"""
            {{
                "id": "5249",
                "created_at": "2024-09-19T14:00:34.069",
                "data": {{
                    "business_name": "{company.name}"
                }}
            }}
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        result = GreatExportEnquiry.objects.get(form_id='5249')
        assert result.company == company
        data = f"""
            {{
                "id": "5250",
                "created_at": "2024-09-19T14:00:34.069",
                "data": {{
                    "company_registration_number": 994349,
                    "business_name": "{company.name}"
                }}
            }}
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        result = GreatExportEnquiry.objects.get(form_id='5250')
        assert result.company == company
        data = f"""
            {{
                "id": "5251",
                "created_at": "2024-09-19T14:00:34.069",
                "data": {{
                    "company_registration_number": "",
                    "business_name": "{company.name}"
                }}
            }}
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        result = GreatExportEnquiry.objects.get(form_id='5251')
        assert result.company == company

    @pytest.mark.django_db
    def test_company_name_mapping_when_duplicates_exist(self):
        """
        Test that when matching company name returns multiple results
        because we already have duplicates in the database any of them
        are assigned, and we assume the duplicate records will be merged
        manually later.
        """
        name = 'duplicate'
        CompanyFactory(name=name, company_number='123')
        CompanyFactory(name=name, company_number='124')
        data = f"""
            {{
                "id": "5249",
                "created_at": "2024-09-19T14:00:34.069",
                "data": {{
                    "business_name": "{name}"
                }}
            }}
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        result = GreatExportEnquiry.objects.get(form_id='5249')
        assert result.company.name == name

    @pytest.mark.django_db
    def test_company_contact_mapping(self):
        """
        Test that Company is mapped correctly based on contact details if
        no Companies House number is matched and the business name is not
        matched
        """
        company = CompanyFactory(company_number='123')
        contact = ContactFactory(company=company)
        name = 'Some non-existent business'
        data = f"""
            {{
                "id": "5249",
                "created_at": "2024-09-19T14:00:34.069",
                "data": {{
                    "company_registration_number": "",
                    "business_name": "{name}",
                    "first_name": "{contact.first_name}",
                    "last_name": "{contact.last_name}",
                    "uk_telephone_number": "{contact.full_telephone_number}",
                    "email": "{contact.email}"
                }}
            }}
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        result = GreatExportEnquiry.objects.get(form_id='5249')
        assert result.company == company

    @pytest.mark.django_db
    def test_unmapped_company(self, caplog):
        """
        Test that when a company can't be mapped based on Companies
        House number, name, or contact, then a new company record
        and a new contact record are created
        """
        name = 'Some non-existent business'
        first_name = 'Ada'
        last_name = 'Babbage'
        email = 'test@example.com'
        phone_number = '07900000000'
        assert not Company.objects.filter(name=name).exists()
        data = f"""
            {{
                "id": "5249",
                "created_at": "2024-09-19T14:00:34.069",
                "data": {{
                    "company_registration_number": "",
                    "business_name": "{name}",
                    "type": "privatelimitedcompany",
                    "number_of_employees": "50-249",
                    "first_name": "{first_name}",
                    "last_name": "{last_name}",
                    "uk_telephone_number": "{phone_number}",
                    "email": "{email}"
                }}
            }}
        """
        task = GreatIngestionTask()
        with caplog.at_level(logging.INFO):
            task.json_to_model(json.loads(data))
            id = Company.objects.latest('created_on').id
            assert 'Could not match company for Great Export Enquiry: 5249.' \
                f'Created new company with id: {id}' in caplog.text
        result = GreatExportEnquiry.objects.get(form_id='5249').company
        assert result.name == name
        expected_size = EmployeeRange.objects.get(name='50 to 249')
        assert result.employee_range == expected_size
        expected_type = BusinessType.objects.get(name='Private limited company')
        assert result.business_type == expected_type
        contact_result = Contact.objects.get(company=result)
        assert contact_result.first_name == first_name
        assert contact_result.last_name == last_name
        assert contact_result.email == email
        assert contact_result.full_telephone_number == phone_number
        assert contact_result.primary is True

    @pytest.mark.django_db
    def test_company_contact_creation(self):
        """
        Test that when the company exists already but the contact doesn't
        the contact is created
        """
        company = CompanyFactory(company_number='123')
        first_name = 'Ada'
        last_name = 'Babbage'
        email = 'test@example.com'
        phone_number = '07900000000'
        assert not Contact.objects.filter(first_name=first_name, last_name=last_name).exists()
        name = 'Some non-existent business'
        data = f"""
            {{
                "id": "5249",
                "created_at": "2024-09-19T14:00:34.069",
                "data": {{
                    "company_registration_number": "{company.company_number}",
                    "business_name": "{name}",
                    "first_name": "{first_name}",
                    "last_name": "{last_name}",
                    "uk_telephone_number": "{phone_number}",
                    "email": "{email}"
                }}
            }}
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        result = GreatExportEnquiry.objects.get(form_id='5249')
        assert result.contact.first_name == first_name
        assert result.contact.last_name == last_name
        assert result.contact.email == email
        assert result.contact.full_telephone_number == phone_number

    @pytest.mark.django_db
    def test_upper_business_size(self):
        """
        Test that the upper business size range is mapped correctly
        """
        name = 'Some non-existent business'
        first_name = 'Ada'
        last_name = 'Babbage'
        email = 'test@example.com'
        phone_number = '07900000000'
        assert not Company.objects.filter(name=name).exists()
        data = f"""
            {{
                "id": "5249",
                "created_at": "2024-09-19T14:00:34.069",
                "data": {{
                    "company_registration_number": "",
                    "business_name": "{name}",
                    "type": "privatelimitedcompany",
                    "number_of_employees": "500plus",
                    "first_name": "{first_name}",
                    "last_name": "{last_name}",
                    "uk_telephone_number": "{phone_number}",
                    "email": "{email}"
                }}
            }}
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        result = GreatExportEnquiry.objects.get(form_id='5249').company
        expected_size = EmployeeRange.objects.get(name='500+')
        assert result.employee_range == expected_size

    @pytest.mark.django_db
    def test_invalid_business_size(self):
        """
        Test that business size that doesn't match our range returns None
        and does not throw an error
        """
        name = 'Some non-existent business'
        first_name = 'Ada'
        last_name = 'Babbage'
        email = 'test@example.com'
        phone_number = '07900000000'
        assert not Company.objects.filter(name=name).exists()
        data = f"""
            {{
                "id": "5249",
                "created_at": "2024-09-19T14:00:34.069",
                "data": {{
                    "company_registration_number": "",
                    "business_name": "{name}",
                    "type": "privatelimitedcompany",
                    "number_of_employees": "50-259",
                    "first_name": "{first_name}",
                    "last_name": "{last_name}",
                    "uk_telephone_number": "{phone_number}",
                    "email": "{email}"
                }}
            }}
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        result = GreatExportEnquiry.objects.get(form_id='5249').company
        assert result.employee_range is None

    @pytest.mark.django_db
    def test_sector_mapping(self):
        """
        Test that sectors are mapped correctly
        """
        primary = Sector.objects.get(segment='Aerospace', level=0)
        secondary = Sector.objects.get(segment='Defence and Security', level=0)
        tertiary = Sector.objects.get(segment='Energy', level=0)
        data = f"""
            {{
                "id": "5249",
                "created_at": "2024-09-19T14:00:34.069",
                "data": {{
                    "sector_primary": "{primary.segment}",
                    "sector_secondary": "{secondary.segment}",
                    "sector_tertiary": "{tertiary.segment}"
                }}
            }}
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        result = GreatExportEnquiry.objects.get(form_id='5249')
        assert result.data_sector_primary == primary
        assert result.data_sector_secondary == secondary
        assert result.data_sector_tertiary == tertiary

    @pytest.mark.django_db
    def test_invalid_sector(self):
        """
        Test that invalid sectors raise a Sentry alert
        """
        data = """
            {
                "id": "5249",
                "created_at": "2024-09-19T14:00:34.069",
                "data": {
                    "sector_primary": "Some non-existent sector",
                    "sector_secondary": ""
                }
            }
        """
        mock_transport = MockSentryTransport()
        init(transport=mock_transport)
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        sentry_event = mock_transport.events[0].get_event()
        expected_message = 'Could not match sector: Some non-existent sector, ' + \
            'for form: 5249'
        assert sentry_event['logentry']['message'] == expected_message

    @pytest.mark.django_db
    def test_invalid_country_code(self):
        """
        Test that when the country code provided in the data file cannot be found
        in the metadata countries table, we save the record with data_country: None
        and trigger a Sentry alert
        """
        data = """
            {
                "id": "5249",
                "created_at": "2024-09-19T14:00:34.069",
                "meta": {
                    "sender": {
                        "country_code": "ZZ"
                    }
                },
                "data": {
                    "markets": ["AR", "ZP", "GB"]
                }
            }
        """
        mock_transport = MockSentryTransport()
        init(transport=mock_transport)
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        result = GreatExportEnquiry.objects.get(form_id='5249')
        argentina = Country.objects.get(name='Argentina')
        uk = Country.objects.get(name='United Kingdom')
        assert result.meta_sender_country is None
        assert list(result.data_markets.all()) == [argentina, uk]
        sentry_event = mock_transport.events[1].get_event()
        expected_message = 'Could not match country with iso code: ZZ, ' + \
            'for form: 5249'
        assert sentry_event['logentry']['message'] == expected_message
        sentry_event = mock_transport.events[0].get_event()
        expected_message = 'Could not match country with iso code: ZP, ' + \
            'for form: 5249'
        assert sentry_event['logentry']['message'] == expected_message

    @pytest.mark.django_db
    def test_boolean_field_mapping(self):
        """
        Test that boolean fields are mapped correctly
        """
        data = """
            {
                "id": "5249",
                "created_at": "2024-09-19T14:00:34.069",
                "data": {
                    "contacted_gov_departments": "no",
                    "received_support": "yes",
                    "help_us_further": null
                }
            }
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        result = GreatExportEnquiry.objects.get(form_id='5249')
        assert result.data_contacted_gov_departments is False
        assert result.data_received_support is True
        assert result.data_help_us_further is None
        data = """
            {
                "id": "5250",
                "created_at": "2024-09-19T14:00:34.069",
                "data": {
                    "contacted_gov_departments": "yes",
                    "help_us_further": ""
                }
            }
        """
        task.json_to_model(json.loads(data))
        result = GreatExportEnquiry.objects.get(form_id='5250')
        assert result.data_contacted_gov_departments is True
        assert result.data_received_support is None
        assert result.data_help_us_further is None

    @pytest.mark.django_db
    @mock_aws
    def test_long_field_values(self, test_file_path):
        """
        Test that we can ingest records with long field values
        """
        initial_count = GreatExportEnquiry.objects.count()
        long_text = (
            'Some text string that is longer than 255 characters.'
            'Testing that because our default Char field storage is'
            'limited to 255 chars so fields with values longer than'
            'that either need to be stored as TextFields if we need'
            'the full value or truncated if we do not. Long long long.'
        )
        data = f"""
            {{
                "id": "5249",
                "created_at": "2024-09-19T14:00:34.069",
                "url": "{long_text}",
                "data": {{
                    "triage_journey": "{long_text}"
                }}
            }}
        """
        task = GreatIngestionTask()
        task.json_to_model(json.loads(data))
        assert GreatExportEnquiry.objects.count() == initial_count + 1
