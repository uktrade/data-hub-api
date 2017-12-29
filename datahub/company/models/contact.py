import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from datahub.core.models import ArchivableModel, BaseModel
from datahub.core.utils import StrEnum
from datahub.metadata import models as metadata_models

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class ContactPermission(StrEnum):
    """Permission codename constants."""

    read_contact = 'read_contact'
    read_contact_document = 'read_contact_document'


class Contact(ArchivableModel, BaseModel):
    """Contact from CDMS."""

    REQUIRED_ADDRESS_FIELDS = (
        'address_1',
        'address_country',
        'address_town'
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.ForeignKey(
        metadata_models.Title, blank=True, null=True, on_delete=models.SET_NULL
    )
    first_name = models.CharField(max_length=MAX_LENGTH)
    last_name = models.CharField(max_length=MAX_LENGTH)
    job_title = models.CharField(max_length=MAX_LENGTH, null=True, blank=True)
    company = models.ForeignKey(
        'Company', related_name='contacts', null=True, blank=True,
        on_delete=models.CASCADE
    )
    adviser = models.ForeignKey(
        'Advisor', related_name='contacts', null=True, blank=True,
        on_delete=models.SET_NULL
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
        on_delete=models.SET_NULL
    )
    address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    telephone_alternative = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    email_alternative = models.EmailField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    archived_documents_url_path = models.CharField(
        max_length=MAX_LENGTH, blank=True,
        help_text='Legacy field. File browser path to the archived documents for this contact.'
    )

    # Marketing preferences
    contactable_by_dit = models.BooleanField(default=False)
    contactable_by_uk_dit_partners = models.BooleanField(default=False)
    contactable_by_overseas_dit_partners = models.BooleanField(default=False)
    accepts_dit_email_marketing = models.BooleanField(default=False)

    # Contact mode preferences
    contactable_by_email = models.BooleanField(default=True)
    contactable_by_phone = models.BooleanField(default=True)

    class Meta:
        permissions = (
            (ContactPermission.read_contact, 'Can read contact'),
            (ContactPermission.read_contact_document, 'Can read contact document'),
        )

    @property
    def name(self):
        """Full name."""
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        """Admin displayed human readable name."""
        return self.name

    def _generate_address_errors(self):
        """Generate per field error."""
        empty_fields = [field for field in self.REQUIRED_ADDRESS_FIELDS
                        if not getattr(self, field)]
        return {field: ['This field may not be null.'] for field in empty_fields}

    def validate_address(self):
        """Custom validation for address.

        Either 'same_as_company' or address_1, address_town and address_country must be defined.
        """
        some_address_fields_existence = any((
            self.address_1,
            self.address_2,
            self.address_town,
            self.address_county,
            self.address_postcode,
            self.address_country
        ))
        all_required_fields_existence = all(
            getattr(self, field) for field in self.REQUIRED_ADDRESS_FIELDS
        )
        if not self.address_same_as_company:
            if some_address_fields_existence and not all_required_fields_existence:
                raise ValidationError(self._generate_address_errors())
            elif not some_address_fields_existence:
                error_message = ('Please select either address_same_as_company or enter an '
                                 'address manually.')
                raise ValidationError({'address_same_as_company': error_message})

    def clean(self):
        """Custom validation."""
        self.validate_address()
        super().clean()

    def save(self, *args, **kwargs):
        """Override the Django save implementation to hook the custom validation."""
        self.clean()
        super().save(*args, **kwargs)
