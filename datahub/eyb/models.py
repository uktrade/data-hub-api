from django.db import models
from django.contrib.postgres.fields import ArrayField

from datahub.core.models import ArchivableModel, BaseModel


class EYBLead(ArchivableModel, BaseModel):
    """EYB Triage and User data combined

    This mirrors the data held in Expand Your Business"""

    # EYB Triage data
    triage_id = models.IntegerField
    triage_hashed_uuid = models.CharField(max_length=200)
    triage_created = models.DateTimeField
    triage_modified = models.DateTimeField
    sector = models.CharField(max_length=255)
    sector_sub = models.CharField(max_length=255, default=None, null=True)
    intent = ArrayField(
        models.CharField(max_length=255),
        size=6,
        default=list,
    )
    intent_other = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    location_city = models.CharField(
        max_length=255, default=None, null=True,
    )
    location_none = models.BooleanField(default=None, null=True)
    hiring = models.CharField(max_length=255)
    spend = models.CharField(max_length=255)
    spend_other = models.CharField(max_length=255, null=True)
    is_high_value = models.BooleanField(default=False)

    # EYB User data
    user_id = models.IntegerField
    user_hashed_uuid = models.CharField(max_length=200)
    user_created = models.DateTimeField
    user_modified = models.DateTimeField
    company_name = models.CharField(max_length=255)
    company_location = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    telephone_number = models.CharField(max_length=255)
    agree_terms = models.BooleanField(default=False)
    agree_info_email = models.BooleanField(default=False)
    landing_timeframe = models.CharField(null=True, default=None, max_length=255)
    company_website = models.CharField(max_length=255, null=True)
