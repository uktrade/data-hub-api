import json
import logging

from smart_open import open

from datahub.company_activity.models import StovaEvents, IngestedFile

logger = logging.getLogger(__name__)
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'


def ingest_stova_data(bucket, file):
    logger.info(f'Ingesting file: {file} started')
    task = StovaEventIngestionTask()
    task.ingest(bucket, file)
    logger.info(f'Ingesting file: {file} finished')


class StovaEventIngestionTask:
    def __init__(self):
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
            self._existing_ids = list(StovaEvents.objects.values_list('event_id', flat=True))
        return int(id) in self._existing_ids

    def json_to_model(self, jsn):
        values = {
            'event_id': jsn.get('id'),
            'url': jsn.get('url'),
            'city': jsn.get('city'),
            'code': jsn.get('code'),
            'name': jsn.get('name'),
            'state': jsn.get('state'),
            'country': jsn.get('submission_type', ''),
            'max_reg': jsn.get('max_reg'),
            'end_date': jsn.get('end_date'),
            'timezone': jsn.get('timezone'),
            'folder_id': jsn.get('folder_id'),
            'live_date': jsn.get('live_date'),
            'close_date': jsn.get('close_date'),
            'created_by': jsn.get('created_by'),
            'price_type': jsn.get('price_type'),
            'start_date': jsn.get('start_date'),
            'description': jsn.get('description'),
            'modified_by': jsn.get('modified_by'),
            'contact_info': jsn.get('contact_info'),
            'created_date': jsn.get('created_date'),
            'location_city': jsn.get('location_city'),
            'location_name': jsn.get('location_name'),
            'modified_date': jsn.get('modified_date'),
            'client_contact': jsn.get('client_contact'),
            'location_state': jsn.get('location_state'),
            'default_language': jsn.get('default_language'),
            'location_country': jsn.get('location_country'),
            'approval_required': jsn.get('approval_required'),
            'location_address1': jsn.get('location_address1'),
            'location_address2': jsn.get('location_address2'),
            'location_address3': jsn.get('location_address3'),
            'location_postcode': jsn.get('location_postcode'),
            'standard_currency': jsn.get('standard_currency'),
        }
        print(values)

        StovaEvents.objects.create(**values)
