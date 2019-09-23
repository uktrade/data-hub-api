import uuid

from django.conf import settings
from django.db import models

from datahub.core import reversion
from datahub.core.models import ArchivableModel, BaseModel
from datahub.core.utils import get_front_end_url, join_truthy_strings, StrEnum
from datahub.metadata import models as metadata_models

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class ContactPermission(StrEnum):
    """Permission codename constants."""

    view_contact = 'view_contact'
    view_contact_document = 'view_contact_document'
    export_contact = 'export_contact'


@reversion.register_base_model()
class Contact(ArchivableModel, BaseModel):
    """
    Contact (a person at a company that DIT has had contact with).

    Additional indexes created via migrations:

        Name: company_contact_upper_email_244368
        Definition: UPPER(email)
        Comments: For when filtering by email__iexact

        Name: company_contact_upper_email_alternative_eb17a977
        Definition: UPPER(email_alternative)
        Comments: For when filtering by email_alternative__iexact
    """

    ADDRESS_VALIDATION_MAPPING = {
        'address_1': {'required': True},
        'address_2': {'required': False},
        'address_town': {'required': True},
        'address_county': {'required': False},
        'address_postcode': {'required': False},
        'address_country': {'required': True},
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.ForeignKey(
        metadata_models.Title, blank=True, null=True, on_delete=models.SET_NULL,
    )
    first_name = models.CharField(max_length=MAX_LENGTH)
    last_name = models.CharField(max_length=MAX_LENGTH)
    job_title = models.CharField(max_length=MAX_LENGTH, null=True, blank=True)
    company = models.ForeignKey(
        'Company', related_name='contacts', null=True, blank=True,
        on_delete=models.CASCADE,
    )
    adviser = models.ForeignKey(
        'Advisor', related_name='contacts', null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    primary = models.BooleanField()
    telephone_countrycode = models.CharField(max_length=MAX_LENGTH)
    telephone_number = models.CharField(max_length=MAX_LENGTH)
    email = models.EmailField()
    address_same_as_company = models.BooleanField(default=False)
    address_1 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    address_2 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    address_town = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    address_county = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    address_country = models.ForeignKey(
        metadata_models.Country, null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    telephone_alternative = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    email_alternative = models.EmailField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    archived_documents_url_path = models.CharField(
        max_length=MAX_LENGTH, blank=True,
        help_text='Legacy field. File browser path to the archived documents for this contact.',
    )

    # Marketing preferences
    accepts_dit_email_marketing = models.BooleanField(default=False)

    def get_absolute_url(self):
        """URL to the object in the Data Hub internal front end."""
        return get_front_end_url(self)

    class Meta:
        permissions = (
            (ContactPermission.view_contact_document.value, 'Can view contact document'),
            (ContactPermission.export_contact.value, 'Can export contact'),
        )
        indexes = [
            # For datasets app which includes API endpoints to be consumed by data-flow
            models.Index(fields=('created_on', 'id')),
        ]

    @property
    def name(self):
        """Full name."""
        return join_truthy_strings(self.first_name, self.last_name)

    def __str__(self):
        """Admin displayed human readable name."""
        company_desc = f'({self.company})' if self.company and self.company.name else ''
        return join_truthy_strings(self.name or '(no name)', company_desc)
