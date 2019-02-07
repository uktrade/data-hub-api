from django.conf import settings
from django.db import models


class MIInvestmentProject(models.Model):
    """
    MI Investment Project model.

    The pipeline is supposed to overwrite data in this table each time it runs.
    If you add or change a column, the next step is to run the pipeline so the data is
    updated (use management command run_pipeline).

    Note: Make sure the table doesn't store any personally identifiable information data.
    """

    dh_fdi_project_id = models.UUIDField(primary_key=True)
    sector_cluster = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    uk_region_name = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    land_date = models.DateField(null=True, blank=True)
    financial_year = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    overseas_region = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    project_url = models.TextField()
    country_url = models.TextField()
    project_fdi_value = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    top_level_sector_name = models.CharField(
        null=True,
        blank=True,
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
    )
    status_collapsed = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    actual_land_date = models.DateField(null=True, blank=True)
    project_reference = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    total_investment = models.DecimalField(blank=True, decimal_places=0, max_digits=19, null=True)
    total_investment_with_zero = models.DecimalField(
        blank=True,
        decimal_places=0,
        max_digits=19,
        null=True,
    )
    number_new_jobs = models.IntegerField(null=True)
    number_new_jobs_with_zero = models.IntegerField(null=True)
    number_safeguarded_jobs = models.IntegerField(null=True)
    number_safeguarded_jobs_with_zero = models.IntegerField(null=True)
    investor_company_country = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    stage_name = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    sector_name = models.TextField(null=True, blank=True)
    archived = models.BooleanField()
    investment_type_name = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    status_name = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    level_of_involvement_name = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    simplified_level_of_involvement = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    possible_uk_region_names = models.CharField(
        null=True,
        blank=True,
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
    )
    actual_uk_region_names = models.CharField(
        null=True,
        blank=True,
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
    )
    estimated_land_date = models.DateField(null=True, blank=True)

    class Meta:
        # The app label is being used for db_router to determine if migrations are allowed
        # because of that resulting table name would have been prefixed with `datahub.`
        # We need to avoid that by explicitly naming the table, as our dashboard software
        # doesn't support table names with a dot.
        db_table = 'mi_dashboard_miinvestmentproject'

        indexes = [
            models.Index(fields=('financial_year',)),
        ]
