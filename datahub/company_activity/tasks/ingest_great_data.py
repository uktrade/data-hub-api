import json

import environ

from smart_open import open

from datahub.company_activity.models import Great

env = environ.Env()
REGION = env('AWS_DEFAULT_REGION')


class GreatIngestionTask:
    def ingest(self, bucket, file):
        path = f's3://{bucket}/{file}'
        for line in open(path):
            jsn = json.loads(line)
            obj = jsn['object']
            attributed_to = obj.get('attributedTo', {})
            meta = obj.get('dit:directoryFormsApi:Submission:Meta', {})
            data = obj.get('dit:directoryFormsApi:Submission:Data', {})
            Great.objects.create(
                form_id=obj['id'],
                published=obj['published'],
                attributed_to_type=attributed_to.get('type', ''),
                attributed_to_id=attributed_to.get('id', ''),
                url=obj.get('url', ''),
                meta_action_name=meta.get('action_name', ''),
                meta_template_id=meta.get('template_id', ''),
                meta_email_address=meta.get('email_address', ''),
                data_comment=data.get('comment', ''),
                data_country=data.get('country', ''),
                data_full_name=data.get('full_name', ''),
                data_website_url=data.get('website_url', ''),
                data_company_name=data.get('company_name', ''),
                data_company_size=data.get('company_size', ''),
                data_phone_number=data.get('phone_number', ''),
                data_email_address=data.get('email_address', ''),
                data_opportunities=data.get('opportunities', ''),
                data_role_in_company=data.get('role_in_company', ''),
                data_opportunity_urls=data.get('opportunity_urls', ''),
            )
