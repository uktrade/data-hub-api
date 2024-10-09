import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from datahub.core import reversion
from datahub.metadata import models as metadata_models

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@reversion.register_base_model()
class Great(models.Model):
    """
    GreatGovUkForms data model

    In Data Workspace these are saved as 3 JSON objects in Postgres (Meta, Data, Actor).
    For the most part we don't validate values as they could be changed without us knowing
    (e.g. accepted submission methods), or are based on user input upstream (e.g. company size).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    form_id = models.IntegerField(unique=True)
    published = models.DateTimeField()

    attributed_to_type = models.CharField(max_length=MAX_LENGTH)
    attributed_to_id = models.CharField(max_length=MAX_LENGTH)

    url = models.CharField(max_length=MAX_LENGTH, null=True)
    meta_action_name = models.CharField(max_length=MAX_LENGTH)
    meta_template_id = models.CharField(max_length=MAX_LENGTH)
    meta_email_address = models.CharField(max_length=MAX_LENGTH)

    data_comment = models.CharField(max_length=MAX_LENGTH)
    data_country = models.ForeignKey(
        metadata_models.Country,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    data_full_name = models.CharField(max_length=MAX_LENGTH)
    data_website_url = models.CharField(max_length=MAX_LENGTH)
    data_company_name = models.CharField(max_length=MAX_LENGTH)
    data_company_size = models.CharField(max_length=MAX_LENGTH)
    data_phone_number = models.CharField(max_length=MAX_LENGTH)
    data_email_address = models.CharField(max_length=MAX_LENGTH)
    data_terms_agreed = models.BooleanField()
    data_opportunities = ArrayField(
        models.CharField(max_length=MAX_LENGTH), default=list,
    )
    data_role_in_company = models.CharField(max_length=MAX_LENGTH)
    # This is a duplicate of opportunities but in the form of a '\n' delimited string
    data_opportunity_urls = models.CharField(max_length=MAX_LENGTH)

    actor_type = models.CharField(max_length=MAX_LENGTH, null=True)
    actor_id = models.IntegerField(null=True)
    actor_dit_email_address = models.CharField(max_length=MAX_LENGTH, null=True)
    actor_dit_is_blacklisted = models.BooleanField(null=True)
    actor_dit_is_whitelisted = models.BooleanField(null=True)
    actor_dit_blacklisted_reason = models.CharField(max_length=MAX_LENGTH, null=True)

    created_on = models.DateTimeField(auto_now_add=True)
