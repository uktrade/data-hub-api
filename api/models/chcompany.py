import uuid
from django.db import models


class CHCompany(models.Model):

    company_number = models.CharField(
        max_length=8,
        null=False,
        blank=False,
        primary_key=True,
        db_index=True,
        verbose_name="Company number")

    company_name = models.CharField(
        max_length=160,
        null=False,
        blank=False,
        verbose_name="Company name")

    registered_address_care_of = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Address care of")

    registered_address_po_box = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name="Address POBox")

    registered_address_address_1 = models.CharField(
        max_length=300,
        null=True,
        blank=True,
        verbose_name="Address line 1 (House number and street")

    registered_address_address_2 = models.CharField(
        max_length=300,
        null=True,
        blank=True,
        verbose_name="Address line 2 (area)")

    registered_address_town = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Address town")

    registered_address_county = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Address county")

    registered_address_country = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Address country")

    registered_address_postcode = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Address postcode")

    company_category = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Company category")

    company_status = models.CharField(
        max_length=70,
        null=True,
        blank=True,
        verbose_name="Company status")

    sic_code_1 = models.CharField(
        max_length=170,
        null=True,
        blank=True)

    sic_code_2 = models.CharField(
        max_length=170,
        null=True,
        blank=True)

    sic_code_3 = models.CharField(
        max_length=170,
        null=True,
        blank=True)

    sic_code_4 = models.CharField(
        max_length=170,
        null=True,
        blank=True)

    uri = models.CharField(
        max_length=100,
        null=True,
        blank=True)

    incorporation_date = models.DateField(
        null=True
    )

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = str(uuid.uuid4())
        models.Model.save(self, *args, **kwargs)
