from typing import Tuple, Type

from django.db.models import F, Model, Value
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet

from datahub.core.query_utils import (
    get_choices_as_case_expression,
    get_empty_string_if_null_expression,
    get_front_end_url_expression,
    get_string_agg_subquery,
)
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.query_utils import get_project_code_expression
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.mi_dashboard.constants import (
    NO_FDI_VALUE_ASSIGNED,
    NO_SECTOR_ASSIGNED,
    NO_UK_REGION_ASSIGNED,
)
from datahub.mi_dashboard.models import MIInvestmentProject
from datahub.mi_dashboard.query_utils import (
    get_collapse_status_name_expression,
    get_country_url,
    get_financial_year_from_land_date_expression,
    get_level_of_involvement_simplified_expression,
    get_other_field_if_null_or_empty_expression,
    get_sector_cluster_expression,
    get_top_level_sector_expression,
)


class ETLBase:
    """
    Generic Extract, Transform and Load.

    This class defines the process of extracting, transforming and loading the data from source
    to destination.

    Source is defined in the `get_source_query` method. That method should return a query that
    provide rows with all the columns specified in the COLUMNS.

    Columns defined in the COLUMNS must also be available in the destination model.

    The `load` method performs loading. It uses `get_rows` method that calls `get_source_query` and
    returns a QuerySet that returns dictionaries with keys specified in the COLUMNS.

    For each dictionary assertion is being made that its keys equal COLUMNS.

    Each dictionary representing a row is then updated or created on the destination database.
    """

    COLUMNS = {}

    def __init__(self, destination: Type[Model], **kwargs):
        """Initialise the destination.

        Destination model needs to have all the columns specified in the COLUMNS.

        :param destination: Model object where the data will be loaded.
        """
        self.destination = destination

    def get_source_query(self) -> QuerySet:
        """
        Get the source query.

        Make sure that the QuerySet provides all the columns specified in the COLUMNS.
        """
        raise NotImplementedError

    def get_rows(self) -> QuerySet:
        """
        Get rows ready to load.

        :returns: a QuerySet that returns dictionaries when used as iterable.
        """
        return self.get_source_query().values(*self.COLUMNS)

    def load(self) -> Tuple[int, int]:
        """
        Load data to the destination table.

        Existing records should be updated.

        :raises: AssertionError if row.keys() != COLUMNS
        :returns: a tuple with number of updated and created records
        """
        updated = 0
        created = 0
        for row in self.get_rows().iterator():
            assert row.keys() == self.COLUMNS, 'Row keys do not match COLUMNS.'

            pk = row.pop(self.destination._meta.pk.name)
            _, is_created = self.destination.objects.update_or_create(
                pk=pk,
                defaults=row,
            )
            updated += int(not is_created)
            created += int(is_created)

        return updated, created


class ETLInvestmentProjects(ETLBase):
    """Extract, Transform and Load Investment Projects."""

    # Columns must exist both in the source query and the destination model.
    COLUMNS = {
        'dh_fdi_project_id',
        'sector_cluster',
        'uk_region_name',
        'land_date',
        'financial_year',
        'overseas_region',
        'project_url',
        'country_url',
        'project_fdi_value',
        'top_level_sector_name',
        'status_collapsed',
        'actual_land_date',
        'project_reference',
        'total_investment',
        'total_investment_with_zero',
        'number_new_jobs',
        'number_new_jobs_with_zero',
        'number_safeguarded_jobs',
        'number_safeguarded_jobs_with_zero',
        'investor_company_country',
        'stage_name',
        'sector_name',
        'archived',
        'investment_type_name',
        'status_name',
        'level_of_involvement_name',
        'simplified_level_of_involvement',
        'possible_uk_region_names',
        'actual_uk_region_names',
        'estimated_land_date',
    }

    def get_source_query(self):
        """Get the query set."""
        return InvestmentProject.objects.annotate(
            # this contains helper annotations
            _possible_uk_region_names=get_string_agg_subquery(
                InvestmentProject,
                'uk_region_locations__name',
            ),
            _actual_uk_region_names=get_string_agg_subquery(
                InvestmentProject,
                'actual_uk_regions__name',
            ),
        ).annotate(
            project_reference=get_project_code_expression(),
            status_name=get_choices_as_case_expression(InvestmentProject, 'status'),
            status_collapsed=get_collapse_status_name_expression(),
            project_url=get_front_end_url_expression('investmentproject', 'pk'),
            sector_name=Coalesce(
                get_sector_name_subquery('sector'),
                Value(NO_SECTOR_ASSIGNED),
            ),
            top_level_sector_name=get_top_level_sector_expression(),
            possible_uk_region_names=Coalesce(
                '_possible_uk_region_names',
                Value(NO_UK_REGION_ASSIGNED),
            ),
            actual_uk_region_names=Coalesce(
                '_actual_uk_region_names',
                Value(NO_UK_REGION_ASSIGNED),
            ),
            project_fdi_value=Coalesce('fdi_value__name', Value(NO_FDI_VALUE_ASSIGNED)),
            sector_cluster=get_sector_cluster_expression('sector'),
            uk_region_name=get_other_field_if_null_or_empty_expression(
                '_actual_uk_region_names',
                '_possible_uk_region_names',
                default=Value(NO_UK_REGION_ASSIGNED),
            ),
            land_date=Coalesce(
                'actual_land_date',
                'estimated_land_date',
            ),
            financial_year=get_financial_year_from_land_date_expression(),
            dh_fdi_project_id=F('id'),
            investment_type_name=get_empty_string_if_null_expression('investment_type__name'),
            level_of_involvement_name=get_empty_string_if_null_expression(
                'level_of_involvement__name',
            ),
            simplified_level_of_involvement=get_level_of_involvement_simplified_expression(),
            overseas_region=get_empty_string_if_null_expression(
                'investor_company__address_country__overseas_region__name',
            ),
            country_url=get_country_url(),
            investor_company_country=get_empty_string_if_null_expression(
                'investor_company__address_country__name',
            ),
            stage_name=F('stage__name'),
            total_investment_with_zero=Coalesce('total_investment', Value(0)),
            number_safeguarded_jobs_with_zero=Coalesce('number_safeguarded_jobs', Value(0)),
            number_new_jobs_with_zero=Coalesce('number_new_jobs', Value(0)),
        )


def run_mi_investment_project_etl_pipeline():
    """Runs FDI dashboard data load."""
    pipeline = ETLInvestmentProjects(destination=MIInvestmentProject)
    return pipeline.load()
