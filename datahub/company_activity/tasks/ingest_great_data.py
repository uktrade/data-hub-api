import json
import logging

from smart_open import open

from datahub.company.models.company import Company
from datahub.company.models.contact import Contact
from datahub.company_activity.models import GreatExportEnquiry, IngestedFile
from datahub.metadata.models import BusinessType, Country, EmployeeRange, Sector

logger = logging.getLogger(__name__)
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'


def ingest_great_data(bucket, file):
    logger.info(f'Ingesting file: {file} started')
    task = GreatIngestionTask()
    task.ingest(bucket, file)
    logger.info(f'Ingesting file: {file} finished')


def validate_company_registration_number(company_registration_number):
    if company_registration_number:
        if len(company_registration_number) > 10:
            return None
    return company_registration_number


class GreatIngestionTask:
    def __init__(self):
        self._countries = None
        self._business_types = None
        self._existing_ids = []

    def ingest(self, bucket, file):
        path = f's3://{bucket}/{file}'
        try:
            with open(path) as s3_file:
                for line in s3_file:
                    jsn = json.loads(line)
                    if not self._already_ingested(jsn.get('id')):
                        self.json_to_model(jsn)
        except Exception as e:
            raise e
        IngestedFile.objects.create(filepath=file)

    def _already_ingested(self, id):
        if not self._existing_ids:
            self._existing_ids = list(GreatExportEnquiry.objects.values_list('form_id', flat=True))
        return int(id) in self._existing_ids

    def _create_company(self, data, form_id):
        company = Company.objects.create(
            name=data.get('business_name', ''),
            company_number=validate_company_registration_number(
                data.get('company_registration_number', ''),
            ),
            turnover_range=self._get_turnover_range(data.get('annual_turnover')),
            business_type=self._get_business_type(data.get('type')),
            employee_range=self._get_business_size(data.get('number_of_employees')),
            address_postcode=data.get('business_postcode', ''),
        )
        logger.info(f'Could not match company for Great Export Enquiry: {form_id}.'
                    f'Created new company with id: {company.id}.')
        self._create_contact(data, company, form_id)
        return company

    def _create_contact(self, data, company, form_id):
        contact = Contact.objects.create(
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            job_title=data.get('job_title', ''),
            full_telephone_number=data.get('uk_telephone_number', ''),
            email=data.get('email', ''),
            primary=True,
            company=company,
        )
        logger.info(f'Could not match contact for Great Export Enquiry: {form_id}.'
                    f'Created new contact with id: {contact.id}.')
        return contact

    def _get_company(self, data, form_id):
        company = self._get_company_by_companies_house_num(
            validate_company_registration_number(data.get('company_registration_number')),
        )
        if company:
            return company
        company = self._get_company_by_name(data.get('business_name'))
        if company:
            return company
        contact = self._get_company_contact(data)
        if contact and contact.company:
            return contact.company
        return self._create_company(data, form_id)

    def _get_company_by_companies_house_num(self, companies_house_num):
        if not companies_house_num:
            return None
        return Company.objects.filter(company_number=companies_house_num).first()

    def _get_company_by_name(self, name):
        if not name:
            return None
        return Company.objects.filter(name=name).first()

    def _get_company_contact(self, data):
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone_number = data.get('uk_telephone_number')
        email = data.get('email')

        contacts = Contact.objects.filter(first_name=first_name, last_name=last_name)
        if phone_number:
            contacts = contacts.filter(full_telephone_number=phone_number)
        if email:
            contacts = contacts.filter(email=email)
        if contacts.exists():
            return contacts.first()

    def _get_business_type(self, business_type_name):
        if self._business_types is None:
            self._business_types = BusinessType.objects.all()
        for type in self._business_types:
            if type.name.replace(' ', '').lower() == business_type_name:
                return type

    def _get_turnover_range(self, turnover):
        return None

    def _get_business_size(self, employees):
        # Expected possible values:
        # https://github.com/uktrade/great-cms/blob/c86ebf688b208eb718fe821bedd7c347ee8165ae/contact/helpers.py#L110
        if not employees:
            return None
        if ('-') in employees:
            employees = ' to '.join(employees.split('-'))
        else:
            employees = employees.replace('plus', '+')
        try:
            return EmployeeRange.objects.get(name=employees)
        except EmployeeRange.DoesNotExist:
            return None

    def _get_sector(self, sector, form_id):
        if not sector:
            return None
        try:
            # The form only allows top level sectors to be selected
            sector = Sector.objects.get(segment=sector, level=0)
            return sector
        except Sector.DoesNotExist:
            logger.exception(
                f'Could not match sector: {sector}, for form: {form_id}',
            )

    def _get_countries(self):
        self._countries = Country.objects.all()

    def _country_from_iso_code(self, country_code, form_id):
        if not country_code or country_code == 'notspecificcountry':
            return None

        if self._countries is None:
            self._get_countries()

        country_code = ' '.join(country_code.split())

        try:
            return self._countries.get(iso_alpha2_code=country_code)
        except Country.DoesNotExist:
            logger.exception(
                f'Could not match country with iso code: {country_code}, for form: {form_id}',
            )

    def _string_to_bool(self, str):
        if str is None:
            return None

        match str.lower().strip():
            case 'yes':
                return True
            case 'no':
                return False
            case _:
                return None

    def json_to_model(self, jsn):
        meta = jsn.get('meta', {})
        sender = meta.get('sender', {})
        data = jsn.get('data', {})
        form_id = jsn['id']
        actor = jsn.get('actor', {})
        if not actor:
            actor_id = None
        else:
            actor_id = actor['id'].split(':')[-1]
        actor_type = actor.get('type', '').split(':')[-1]
        actor_blacklisted_reason = str(actor.get('dit:blackListedReason', '') or '')
        markets = []
        for country_code in data.get('markets', []):
            country = self._country_from_iso_code(country_code, form_id)
            if country:
                markets.append(country)
        company = self._get_company(data, form_id)
        contact = self._get_company_contact(data)
        if not contact:
            contact = self._create_contact(data, company, form_id)

        values = {
            'form_id': form_id,
            'url': str(jsn.get('url', '') or ''),
            'form_created_at': jsn.get('created_at'),
            'submission_type': jsn.get('submission_action', ''),
            'submission_action': jsn.get('submission_type', ''),
            'company': company,
            'contact': contact,

            'meta_sender_ip_address': meta.get('sender_ip_address', ''),
            'meta_sender_country': self._country_from_iso_code(
                sender.get('country_code', None), form_id,
            ),
            'meta_sender_email_address': meta.get('sender_email_address', ''),
            'meta_subject': meta.get('subject', ''),
            'meta_full_name': meta.get('full_name', ''),
            'meta_subdomain': meta.get('subdomain', ''),
            'meta_action_name': meta.get('action_name', ''),
            'meta_service_name': meta.get('service_name', ''),
            'meta_spam_control': meta.get('spam_control', ''),
            'meta_email_address': meta.get('email_address', ''),

            'data_search': data.get('search', ''),
            'data_enquiry': data.get('enquiry', ''),
            'data_find_out_about': data.get('find_out_about', ''),
            'data_sector_primary': self._get_sector(
                data.get('sector_primary', None),
                form_id,
            ),
            'data_sector_secondary': self._get_sector(
                data.get('sector_secondary', None),
                form_id,
            ),
            'data_sector_tertiary': self._get_sector(
                data.get('sector_tertiary', None),
                form_id,
            ),
            'data_sector_primary_other': data.get('sector_primary_other', ''),
            'data_triage_journey': data.get('triage_journey', ''),
            'data_received_support': self._string_to_bool(
                data.get('received_support', None),
            ),
            'data_product_or_service_1': data.get('product_or_service_1', ''),
            'data_product_or_service_2': data.get('product_or_service_2', ''),
            'data_product_or_service_3': data.get('product_or_service_3', ''),
            'data_product_or_service_4': data.get('product_or_service_4', ''),
            'data_product_or_service_5': data.get('product_or_service_5', ''),
            'data_about_your_experience': data.get('about_your_experience', ''),
            'data_contacted_gov_departments': self._string_to_bool(
                data.get('contacted_gov_departments', None),
            ),
            'data_help_us_further': self._string_to_bool(
                data.get('help_us_further', ''),
            ),
            'data_help_us_improve': data.get('help_us_improve', ''),

            'actor_type': actor_type,
            'actor_id': actor_id,
            'actor_dit_email_address': actor.get('dit:emailAddress', ''),
            'actor_dit_is_blacklisted': actor.get('dit:isBlacklisted', None),
            'actor_dit_is_whitelisted': actor.get('dit:isWhitelisted', None),
            'actor_dit_blacklisted_reason': actor_blacklisted_reason,
        }
        obj = GreatExportEnquiry.objects.create(**values)
        obj.data_markets.set(markets)
