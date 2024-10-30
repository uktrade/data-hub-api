import uuid

from django.conf import settings
from django.db import models

from datahub.company.models.company import Company
from datahub.core import reversion
from datahub.metadata import models as metadata_models

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@reversion.register_base_model()
class GreatExportEnquiry(models.Model):
    """
    GreatGovUkForms Export Enquiry data model

    In Data Workspace these are saved as 3 JSON objects in Postgres (Meta, Data, Actor).
    For the most part we don't validate values as they could be changed without us knowing
    (e.g. accepted submission methods), or are based on user input upstream (e.g. company size).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    form_id = models.IntegerField(unique=True)
    url = models.TextField()
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='great_export_enquiries',
    )

    meta_sender_ip_address = models.CharField(max_length=MAX_LENGTH)
    meta_sender_country = models.ForeignKey(
        metadata_models.Country,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='great_export_enquiries',
    )
    meta_sender_email_address = models.CharField(max_length=MAX_LENGTH)
    meta_subject = models.CharField(max_length=MAX_LENGTH)
    meta_full_name = models.CharField(max_length=MAX_LENGTH)
    meta_subdomain = models.CharField(max_length=MAX_LENGTH)
    meta_action_name = models.CharField(max_length=MAX_LENGTH)
    meta_service_name = models.CharField(max_length=MAX_LENGTH)
    meta_spam_control = models.CharField(max_length=MAX_LENGTH)
    meta_email_address = models.CharField(max_length=MAX_LENGTH)

    data_search = models.CharField(max_length=MAX_LENGTH)
    data_enquiry = models.CharField(max_length=MAX_LENGTH)
    data_markets = models.ManyToManyField(
        metadata_models.Country,
        related_name='great_export_market_enquiries',
    )
    data_find_out_about = models.CharField(max_length=MAX_LENGTH)
    data_sector_primary = models.CharField(max_length=MAX_LENGTH)
    data_sector_primary = models.ForeignKey(
        metadata_models.Sector,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='great_export_primary_sector_enquiries',
    )
    data_sector_secondary = models.ForeignKey(
        metadata_models.Sector,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='great_export_secondary_sector_enquiries',
    )
    data_sector_tertiary = models.ForeignKey(
        metadata_models.Sector,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='great_export_tertiary_sector_enquiries',
    )
    data_sector_primary_other = models.CharField(max_length=MAX_LENGTH)
    data_triage_journey = models.TextField()
    data_received_support = models.BooleanField(null=True)
    data_uk_telephone_number = models.CharField(max_length=MAX_LENGTH)
    data_product_or_service_1 = models.CharField(max_length=MAX_LENGTH)
    data_product_or_service_2 = models.CharField(max_length=MAX_LENGTH)
    data_product_or_service_3 = models.CharField(max_length=MAX_LENGTH)
    data_product_or_service_4 = models.CharField(max_length=MAX_LENGTH)
    data_product_or_service_5 = models.CharField(max_length=MAX_LENGTH)
    data_about_your_experience = models.CharField(max_length=MAX_LENGTH)
    data_contacted_gov_departments = models.BooleanField(null=True)
    data_help_us_further = models.BooleanField(null=True)
    data_help_us_improve = models.CharField(max_length=MAX_LENGTH)

    actor_id = models.IntegerField(null=True)
    actor_type = models.CharField(max_length=MAX_LENGTH, null=True)
    actor_dit_email_address = models.CharField(max_length=MAX_LENGTH, null=True)
    actor_dit_is_blacklisted = models.BooleanField(null=True)
    actor_dit_is_whitelisted = models.BooleanField(null=True)
    actor_dit_blacklisted_reason = models.CharField(max_length=MAX_LENGTH, null=True)

    form_created_at = models.DateTimeField()
    actor_email = models.CharField(max_length=MAX_LENGTH)
    submission_type = models.CharField(max_length=MAX_LENGTH)
    submission_action = models.CharField(max_length=MAX_LENGTH)
    created_on = models.DateTimeField(auto_now_add=True)
