import json
import logging

import environ

from smart_open import open

from datahub.company_activity.models import Great, IngestedFile
from datahub.metadata.models import Country

logger = logging.getLogger(__name__)
env = environ.Env()
REGION = env('AWS_DEFAULT_REGION', default='eu-west-2')


def ingest_great_data(bucket, file):
    logger.info(f'Ingesting file: {file} started')
    task = GreatIngestionTask()
    task.ingest(bucket, file)
    logger.info(f'Ingesting file: {file} finished')


class GreatIngestionTask:
    def __init__(self):
        self._countries = None

    def ingest(self, bucket, file):
        path = f's3://{bucket}/{file}'
        try:
            with open(path) as s3_file:
                for line in s3_file:
                    self.json_to_model(json.loads(line))
        except Exception as e:
            raise e
        IngestedFile.objects.create(filepath=file)

    def _get_countries(self):
        self._countries = Country.objects.all()

    def country_from_iso_code(self, country_code, form_id):
        if not country_code:
            return None

        if self._countries is None:
            self._get_countries()

        try:
            return self._countries.get(iso_alpha2_code=country_code)
        except Country.DoesNotExist:
            logger.exception(
                f'Could not match country with iso code: {country_code}, for form: {form_id}',
            )

    def json_to_model(self, jsn):
        obj = jsn['object']
        attributed_to = obj.get('attributedTo', {})
        meta = obj.get('dit:directoryFormsApi:Submission:Meta', {})
        data = obj.get('dit:directoryFormsApi:Submission:Data', {})
        form_id = obj['id'].split(':')[-1]
        attributed_to_type = attributed_to.get('type', ':').split(':')[-1]
        attributed_to_id = attributed_to.get('id', ':').split(':')[-1]
        actor = jsn.get('actor', {})
        if not actor:
            actor_id = None
            actor_type = None
        else:
            actor_id = actor['id'].split(':')[-1]
            actor_type = actor['type'].split(':')[-1]
        values = {
            'published': obj['published'],
            'url': obj.get('url', ''),

            'attributed_to_type': attributed_to_type,
            'attributed_to_id': attributed_to_id,

            'meta_action_name': meta.get('action_name', ''),
            'meta_template_id': meta.get('template_id', ''),
            'meta_email_address': meta.get('email_address', ''),

            'data_comment': data.get('comment', ''),
            'data_country': self.country_from_iso_code(data.get('country', ''), form_id),
            'data_full_name': data.get('full_name', ''),
            'data_website_url': data.get('website_url', ''),
            'data_company_name': data.get('company_name', ''),
            'data_company_size': data.get('company_size', ''),
            'data_phone_number': data.get('phone_number', ''),
            'data_email_address': data.get('email_address', ''),
            'data_terms_agreed': data.get('terms_agreed', False),
            'data_opportunities': data.get('opportunities', []),
            'data_role_in_company': data.get('role_in_company', ''),
            'data_opportunity_urls': data.get('opportunity_urls', ''),

            'actor_type': actor_type,
            'actor_id': actor_id,
            'actor_dit_email_address': actor.get('dit:emailAddress', None),
            'actor_dit_is_blacklisted': actor.get('dit:isBlacklisted', None),
            'actor_dit_is_whitelisted': actor.get('dit:isWhitelisted', None),
            'actor_dit_blacklisted_reason': actor.get('dit:blackListedReason', None),
        }
        Great.objects.update_or_create(
            form_id=form_id,
            defaults=values,
        )
