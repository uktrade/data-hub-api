import uuid

from django.conf import settings
from django.db import models

from datahub.core import reversion

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@reversion.register_base_model()
class Great(models.Model):
    """
    GreatGovUkForms data model
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    form_id = models.CharField(max_length=MAX_LENGTH)
    published = models.DateTimeField()

    attributed_to_type = models.CharField(max_length=MAX_LENGTH)
    attributed_to_id = models.CharField(max_length=MAX_LENGTH)

    url = models.CharField(max_length=MAX_LENGTH)
    meta_action_name = models.CharField(max_length=MAX_LENGTH)
    meta_template_id = models.CharField(max_length=MAX_LENGTH)
    meta_email_address = models.CharField(max_length=MAX_LENGTH)

    data_comment = models.CharField(max_length=MAX_LENGTH)
    data_country = models.CharField(max_length=MAX_LENGTH)
    data_full_name = models.CharField(max_length=MAX_LENGTH)
    data_website_url = models.CharField(max_length=MAX_LENGTH)
    data_company_name = models.CharField(max_length=MAX_LENGTH)
    data_company_size = models.CharField(max_length=MAX_LENGTH)
    data_phone_number = models.CharField(max_length=MAX_LENGTH)
    data_email_address = models.CharField(max_length=MAX_LENGTH)
    data_terms_agreed = models.BooleanField()
    data_opportunities = models.CharField(max_length=MAX_LENGTH)
    data_role_in_company = models.CharField(max_length=MAX_LENGTH)
    data_opportunity_urls = models.CharField(max_length=MAX_LENGTH)

    created_on = models.DateTimeField(auto_now_add=True)
