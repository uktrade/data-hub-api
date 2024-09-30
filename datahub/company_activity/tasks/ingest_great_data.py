import json

import environ

from smart_open import open

from datahub.company_activity.models import Great
from datahub.metadata.models import Country

env = environ.Env()
REGION = env('AWS_DEFAULT_REGION', default='eu-west-2')


class GreatIngestionTask:
    def ingest(self, bucket, file):
        path = f's3://{bucket}/{file}'
        countries = Country.objects.all()
        try:
            for line in open(path):
                jsn = json.loads(line)
                obj = jsn['object']
                attributed_to = obj.get('attributedTo', {})
                meta = obj.get('dit:directoryFormsApi:Submission:Meta', {})
                data = obj.get('dit:directoryFormsApi:Submission:Data', {})
                actor = obj.get('actor', {})
                country_code = data.get('country', '')
                Great.objects.create(
                    form_id=obj['id'],
                    published=obj['published'],
                    url=obj.get('url', ''),

                    attributed_to_type=attributed_to.get('type', ''),
                    attributed_to_id=attributed_to.get('id', ''),

                    meta_action_name=meta.get('action_name', ''),
                    meta_template_id=meta.get('template_id', ''),
                    meta_email_address=meta.get('email_address', ''),

                    data_comment=data.get('comment', ''),
                    data_country=countries.filter(iso_alpha2_code=country_code).first(),
                    data_full_name=data.get('full_name', ''),
                    data_website_url=data.get('website_url', ''),
                    data_company_name=data.get('company_name', ''),
                    # Should this allow only pre-defined values?
                    data_company_size=data.get('company_size', ''),
                    data_phone_number=data.get('phone_number', ''),
                    data_email_address=data.get('email_address', ''),
                    data_terms_agreed=data.get('terms_agreed', False),
                    # Should this be a list rather than a string?
                    data_opportunities=data.get('opportunities', ''),
                    data_role_in_company=data.get('role_in_company', ''),
                    data_opportunity_urls=data.get('opportunity_urls', ''),

                    actor_type=actor.get('type', ''),
                    actor_id=actor.get('id', ''),
                    actor_dit_email_address=actor.get('dit:emailAddress', ''),
                    actor_dit_is_blacklisted=actor.get('dit:isBlacklisted', False),
                    actor_dit_is_whitelisted=actor.get('dit:isWhitelisted', False),
                    actor_dit_blacklisted_reason=actor.get('dit:blackListedReadon', ''),
                )
        except Exception as e:
            raise e
