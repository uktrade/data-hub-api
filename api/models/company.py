import uuid
from django.db import models


class Company(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company_number = models.CharField(
        max_length=8,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Company number",
        help_text="The company number for companies filed with companies house so they can be displayed if provided.")

    uk_based = models.BooleanField(
        default=True
    )

    business_type = models.CharField(
        max_length=160,
        null=False,
        blank=False,
        verbose_name="Business type",
        help_text="The classification of the business type, e.g. Private Limited Company",
        choices=(
            ("Business partnership", "Business partnership"),
            ("Private limited company", "Private limited company"),
            ("Public limited company", "Public limited company"),
            ("Sole trader", "Sole trader"),
        )
    )

    registered_name = models.CharField(
        max_length=160,
        null=False,
        blank=False,
        verbose_name="Registered name")

    trading_name = models.CharField(
        max_length=160,
        null=True,
        blank=True,
        help_text="The name the company trades as, if this differs from the name it is registered as",
        verbose_name="Trading name")

    sectors = models.TextField(
        null=True,
        blank=True,
        help_text="A comma separated list of business sectors the company belongs to, e.g. Aerospace"
    )

    website = models.URLField(
        null=True,
        blank=True,
        verbose_name="Website",
        help_text="Does the company have a website?"
    )

    number_of_employees = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Number of employees",
        choices=(
            ("1 to 9", "1 to 9"),
            ("10 to 49", "10 to 49"),
            ("50 to 249", "50 to 249"),
            ("500+", "500+"),
        )
    )

    annual_turnover = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Annual turnover",
        choices=(
            ("£0 to £1.34M", "£0 to £1.34M"),
            ("£1.34M to £6.7M", "£1.34M to £6.7M"),
            ("£6.7M to £33.5M", "£6.7M to £33.5M"),
            ("£33.5M +", "£33.5M +"),
        )
    )

    trading_address_1 = models.CharField(
        max_length=300,
        null=True,
        blank=True,
        verbose_name="Address line 1 (House number and street")

    trading_address_2 = models.CharField(
        max_length=300,
        null=True,
        blank=True,
        verbose_name="Address line 2 (area)")

    trading_address_town = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Address town")

    trading_address_county = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Address county")

    trading_address_country = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Address country")

    trading_address_postcode = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Address postcode")

    region = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Region",
        help_text="The region responsible for this company, e.g. North-East"
    )

    account_manager = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Account manger")

    countries_of_interest = models.TextField(
        null=True,
        blank=True,
        help_text="A comma separated list of countries the company has expressed an interest in exporting to."
    )

    currently_exporting_to = models.TextField(
        null=True,
        blank=True,
        help_text="A comma separated list of countries the company is already exporting to."
    )

    # Introduced early in the prototype, hoping at some point this will be used to describe company relationshipsips
    connections = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )

    business_description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Description",
        help_text="A brief description of this company and what it does or things to be considered."
    )

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.registered_name
