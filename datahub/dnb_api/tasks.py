from celery import shared_task
from celery.utils.log import get_task_logger
from rest_framework.status import is_server_error

from datahub.company.models import Company
from datahub.dnb_api.utils import (
    DNBServiceConnectionError,
    DNBServiceError,
    get_company,
    update_company_from_dnb,
)

logger = get_task_logger(__name__)


def _sync_company_with_dnb(company_id, fields_to_update, task):
    dh_company = Company.objects.get(id=company_id)

    try:
        dnb_company = get_company(dh_company.duns_number)
    except DNBServiceError as exc:
        if is_server_error(exc.status_code):
            raise task.retry(exc=exc, countdown=60)
        raise
    except DNBServiceConnectionError as exc:
        raise task.retry(exc=exc, countdown=60)

    update_company_from_dnb(
        dh_company,
        dnb_company,
        fields_to_update=fields_to_update,
        update_descriptor='celery:sync_company_with_dnb',
    )


@shared_task(
    bind=True,
    acks_late=True,
    priority=9,
    max_retries=3,
)
def sync_company_with_dnb(self, company_id, fields_to_update=None):
    """
    Sync a company record with data sourced from DNB. `company_id` identifies the
    company record to sync and `fields_to_update` defines an iterable of
    company serializer fields that should be updated - if it is None, all fields
    will be synced.
    """
    _sync_company_with_dnb(company_id, fields_to_update, self)
