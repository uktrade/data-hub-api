import logging

from django.db.models.signals import post_migrate
from django.dispatch import receiver

from datahub.company.constants import BusinessTypeConstant
from datahub.core.utils import load_constants_to_database
from datahub.metadata.models import BusinessType

logger = logging.getLogger(__name__)


@receiver(
    post_migrate,
    sender=BusinessType._meta.app_config,
    dispatch_uid='company_business_type_post_migrate',
)
def company_business_type_post_migrate(sender, **kwargs):
    """
    Ensures all business types are loaded to the database.

    Any new business types are created, and any existing ones are updated if the label has changed.
    """
    load_constants_to_database(BusinessTypeConstant, BusinessType)
