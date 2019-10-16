import uuid

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.postgres.fields import CICharField
from django.core.mail import send_mail
from django.db import models
from django.utils.functional import cached_property
from django.utils.timezone import now

from datahub.core import reversion
from datahub.core.utils import join_truthy_strings
from datahub.metadata import models as metadata_models

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class AdviserManager(BaseUserManager):
    """Django user manager made friendly to not having username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Creates and saves a User with the given username, email and password."""
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create user."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create super user."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


@reversion.register_base_model(extra_exclude=('last_login',))
class Advisor(AbstractBaseUser, PermissionsMixin):
    """Adviser model.

    Advisor is a legacy name mistakenly used, but hard to change now.

    Additional indexes created via migrations:

        Name: company_advisor_is_active_upper_name_e0ab1b4f
        Definition: ("is_active", (UPPER("first_name" || ' ' || "last_name" )))
        Comments: Used by the import interactions tool when looking up an active adviser by name
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    # Used as a username. In many cases this is not the user's actual email address. Some do not
    # pass Django's EmailValidator so CICharField is used here.
    email = CICharField(max_length=MAX_LENGTH, unique=True, verbose_name='username')
    first_name = models.CharField(max_length=MAX_LENGTH, blank=True)
    last_name = models.CharField(max_length=MAX_LENGTH, blank=True)
    telephone_number = models.CharField(max_length=MAX_LENGTH, blank=True)
    contact_email = models.EmailField(max_length=MAX_LENGTH, blank=True)
    dit_team = models.ForeignKey(
        metadata_models.Team, blank=True, null=True, on_delete=models.SET_NULL,
    )
    is_staff = models.BooleanField(
        'staff status',
        default=False,
        help_text='Designates whether the user can log into this admin site.',
    )
    is_active = models.BooleanField(
        'active',
        default=True,
        help_text=(
            'Designates whether this user should be treated as active. '
            'Deselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField('date joined', default=now)

    objects = AdviserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    @cached_property
    def name(self):
        """Full name shorthand."""
        return join_truthy_strings(self.first_name, self.last_name)

    def __str__(self):
        """Admin displayed human readable name."""
        return self.name or '(no name)'

    # Django User methods, required for Admin interface

    def get_full_name(self):
        """Returns the first_name plus the last_name, with a space in between."""
        return self.name.strip()

    def get_short_name(self):
        """Returns the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Sends an email to this User."""
        send_mail(subject, message, from_email, [self.get_current_email()], **kwargs)

    def get_current_email(self):
        """
        :returns: the most up-to-date email address for this adviser.
        """
        return self.contact_email or self.email

    def get_email_domain(self):
        """
        :returns: Domain for adviser's current email.
        """
        email = self.get_current_email()
        try:
            _, domain = email.rsplit('@', maxsplit=1)
        except ValueError:
            return None
        return domain.lower()

    class Meta:
        indexes = [
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['date_joined', 'id']),
        ]
        verbose_name = 'adviser'
