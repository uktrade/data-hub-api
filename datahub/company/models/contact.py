import uuid

from django.conf import settings
from django.db import models
from django.utils.timezone import now

from datahub.core import reversion
from datahub.core.models import ArchivableModel, BaseModel
from datahub.core.utils import get_front_end_url, join_truthy_strings, StrEnum
from datahub.core.validators import (
    InternationalTelephoneValidator,
)
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
    """

    class TransferReason(models.TextChoices):
        DUPLICATE = ('duplicate', 'Duplicate record')

    ADDRESS_VALIDATION_MAPPING = {
        'address_1': {'required': True},
        'address_2': {'required': False},
        'address_town': {'required': True},
        'address_county': {'required': False},
        'address_postcode': {'required': False},
        'address_area': {'required': False},
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

    full_telephone_number = models.CharField(
        validators=[InternationalTelephoneValidator()],
        max_length=MAX_LENGTH,
        blank=True,
    )
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
    address_area = models.ForeignKey(
        metadata_models.AdministrativeArea,
        related_name='contacts',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
    notes = models.TextField(null=True, blank=True)
    archived_documents_url_path = models.CharField(
        max_length=MAX_LENGTH, blank=True,
        help_text='Legacy field. File browser path to the archived documents for this contact.',
    )
    valid_email = models.BooleanField(null=True, blank=True)
    transferred_to = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='transferred_from',
        help_text='Where data about this company was transferred to.',
    )
    transfer_reason = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        choices=TransferReason.choices,
        help_text='The reason data for this company was transferred.',
    )
    transferred_on = models.DateTimeField(blank=True, null=True)
    transferred_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

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

    def __str__(self):
        """Admin displayed human readable name."""
        company_desc = f'({self.company})' if self.company and self.company.name else ''
        return join_truthy_strings(self.name or '(no name)', company_desc)

    @property
    def name(self):
        """Full name."""
        return join_truthy_strings(self.first_name, self.last_name)

    @property
    def name_with_title(self):
        """Full name with title."""
        return join_truthy_strings(getattr(self.title, 'name', None), self.name)

    def mark_as_transferred(self, to, reason, user):
        """
        Marks a contact record as having been transferred to another contact record.
        This is used, for example, for marking a contact as a duplicate record.
        """
        self.modified_by = user
        self.transfer_reason = reason
        self.transferred_by = user
        self.transferred_on = now()
        self.transferred_to = to

        display_reason = self.get_transfer_reason_display()

        archived_reason = (
            f'This record is no longer in use and its data has been transferred to {to} for the '
            f'following reason: {display_reason}.'
        )

        # Note: archive() saves the model instance
        self.archive(user, archived_reason)

    def merge_contact_fields(self, contact):

        fields = [
            'job_title',
            'title',
            'full_telephone_number',
            'notes',
            'archived_documents_url_path',
            'valid_email',
            'company',
            'adviser',
        ]

        for field in fields:
            contact_field_value = getattr(contact, field)
            source_field_value = getattr(self, field)

            if not source_field_value and contact_field_value:
                setattr(self, field, contact_field_value)

        address_fields = [
            'address_1',
            'address_2',
            'address_town',
            'address_postcode',
            'address_county',
            'address_country',
            'address_area',
        ]

        if not self.address_1 and not self.address_same_as_company:
            if contact.address_1:
                for field in address_fields:
                    contact_address_value = getattr(contact, field)
                    setattr(self, field, contact_address_value)
            elif contact.address_same_as_company:
                self.address_same_as_company = contact.address_same_as_company
