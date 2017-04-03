# pip install boto3
# Run inside manage.py shell_plus

from collections import namedtuple, OrderedDict
from logging import getLogger

import boto3

from datahub.interaction.models import ServiceDelivery
from loading_scripts import utils


logger = getLogger(__name__)


s3 = boto3.resource(
    's3',
    region_name='eu-west-2',
    aws_access_key_id='foo',
    aws_secret_access_key='bar',
)
s3_bucket = s3.Bucket('cornelius.dev.uktrade.io')


def extract(bucket, entity_name, spec):
    """Extract data from bucket using given prefix and mapping spec."""
    row_mapping = namedtuple('row_mapping', spec.values())

    def get_by_path(srcdict, path):
        value = srcdict
        for chunk in path.split('.'):
            value = value[chunk]

        return value

    ret = set()

    for row in utils.iterate_over_cdms_entities_from_s3(bucket, entity_name):
        ret.add(row_mapping(
            *(get_by_path(row, field) for field in spec.keys())
        ))

    return ret


spec_model = ServiceDelivery
spec = OrderedDict([
    ('optevia_servicedeliveryId', 'id'),
    ('optevia_Event.Id', 'event_id'),
    ('optevia_ServiceProvider.Id', 'dit_team_id'),
    ('optevia_Service.Id', 'service_id'),
    ('optevia_Contact.Id', 'contact_id'),
    ('optevia_LeadCountry.Id', 'country_of_interest_id'),
    ('optevia_Advisor.Id', 'dit_advisor_id'),
    ('optevia_Sector.Id', 'sector_id'),
    ('optevia_Organisation.Id', 'company_id'),
    ('optevia_ServiceDeliveryStatus.Id', 'status_id'),
    ('optevia_UKRegion.Id', 'uk_region_id'),
    ('optevia_ServiceOffer.Id', 'service_offer_id'),
    ('optevia_OrderDate', 'date'),
    ('optevia_Notes', 'notes'),
    ('optevia_name', 'subject'),
])

# spec_model = Event
# spec = OrderedDict([
#     ('optevia_eventId', 'id'),
#     ('optevia_name', 'name'),
# ])

# spec_model = ServiceOffer
# spec = OrderedDict([
#     ('optevia_serviceofferId', 'id'),
#     ('optevia_Event.Id', 'event_id'),
#     ('optevia_Service.Id', 'service_id'),
#     ('optevia_ServiceProvider.Id', 'dit_team_id'),
# ])

res = extract(
    s3_bucket,
    'optevia_servicedeliverySet',
    # 'optevia_eventSet',
    # 'optevia_serviceofferSet',
    spec,
)

for i, row in enumerate(res):
    if i % 100 == 0:
        print(i)  # noqa: T003

    try:
        data = row._asdict()
        data['date'] = utils.cdms_datetime_to_datetime(data['date'])
        data['notes'] = data['notes'] or ''
        obj_id = data.pop('id')
        obj, created = spec_model.objects.get_or_create(
            id=obj_id, defaults=data
        )
        if not created:
            for name, value in data.items():
                setattr(obj, name, value)
            obj.save()

    except Exception as e:
        logger.exception('Exception during importing data')
