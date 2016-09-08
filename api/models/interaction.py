import uuid
from django.db import models

from api.models.company import Company
from api.models.contact import Contact


class Interaction(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    interaction_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Title")

    subject = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Subject")

    date_of_interaction = models.DateField(null = False)

    advisor = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Adviser")

    notes = models.TextField(null=True, blank=True)

    company = models.ForeignKey(
        to=Company,
        null=True,
        related_name="interactions")

    contact = models.ForeignKey(
        to=Contact,
        null=True,
        related_name="interactions")
