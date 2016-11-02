import uuid

from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.utils.functional import cached_property

from company.models import MAX_LENGTH
from core.mixins import DeferredSaveModelMixin


class Advisor(DeferredSaveModelMixin, models.Model):
    """Advisor."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, db_index=True, default=uuid.uuid4)
    first_name = models.CharField(max_length=MAX_LENGTH)
    last_name = models.CharField(max_length=MAX_LENGTH)
    dit_team = models.ForeignKey('company.Team')
    email = models.EmailField()

    @cached_property
    def name(self):
        return '{first_name} {last_name}'.format(first_name=self.first_name, last_name=self.last_name)

    def save(self, use_korben=True, *args, **kwargs):
        """Create a user with an unusable password"""

        if not self.user:
            self.user = User.objects.create(
                email=self.email,
                first_name=self.first_name,
                last_name=self.last_name,
                username=self.email.split('@')[0],
            )
            self.user.set_unusable_password()

        super().save(use_korben=use_korben, *args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'company_advisor'  # legacy for the ETL
