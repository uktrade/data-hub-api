from django.conf import settings
from django.db.models import (
    Case,
    CharField,
    DateField,
    DurationField,
    F,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Cast, Coalesce, Concat, ExtractYear, NullIf

from datahub.investment.project.constants import Involvement
from datahub.investment.project.models import IProjectAbstract
from datahub.metadata.models import Sector
from datahub.mi_dashboard.constants import NO_SECTOR_ASSIGNED, NO_SECTOR_CLUSTER_ASSIGNED


def get_level_of_involvement_simplified_expression():
    """Get expression to map level of involvement into simplified version."""
    # TODO: this logic duplicates level_of_involvement_simplified property logic in the
    # InvestmentProject model.
    return Case(
        When(
            level_of_involvement_id=None,
            then=Value(IProjectAbstract.INVOLVEMENT.unspecified),
        ),
        When(
            level_of_involvement_id=Involvement.no_involvement.value.id,
            then=Value(IProjectAbstract.INVOLVEMENT.not_involved),
        ),
        When(
            ~Q(level_of_involvement_id=Involvement.no_involvement.value.id),
            then=Value(IProjectAbstract.INVOLVEMENT.involved),
        ),
        output_field=CharField(),
    )


def get_top_level_sector_expression():
    """Get top-level sector value."""
    subquery = Sector.objects.filter(
        parent_id__isnull=True,
        tree_id=OuterRef('sector__tree_id'),
    ).values('segment')

    return Coalesce(
        Subquery(subquery, output_field=CharField()),
        Value(NO_SECTOR_ASSIGNED),
    )


def get_sector_cluster_expression(field):
    """Get sector cluster value."""
    subquery = Sector.objects.filter(
        parent_id__isnull=True,
        tree_id=OuterRef(f'{field}__tree_id'),
    ).values('sector_cluster__name')

    return Coalesce(
        Subquery(subquery, output_field=CharField()),
        Value(NO_SECTOR_CLUSTER_ASSIGNED),
    )


def get_collapse_status_name_expression():
    """
    Map status_name to status_collapsed.

    If investment project status_name is either Ongoing or Won, status_collapsed will be
    Ongoing / Won.
    """
    return Case(
        When(
            Q(status_name='Ongoing') | Q(status_name='Won'),
            then=Value('Ongoing / Won'),
        ),
        default='status_name',
    )


def get_other_field_if_null_or_empty_expression(field_a, field_b, default=None):
    """
    Get other field_b value if field_a is null or empty.

    If field_b is null, return empty string.
    """
    return Coalesce(
        NullIf(field_a, Value('')),
        field_b,
        default,
    )


def get_financial_year_from_land_date_expression():
    """
    Extract financial year from the land_date field.

    Fiscal financial year starts on April the 1th and ends on the 31st March the following year. To
    simplify the calculation of the financial year, we need to offset the date by
    3 months so for example the date 7th April 2015 becomes 7th January 2015 and the
    year becomes the start year of the calculated financial year.
    """
    adjusted_land_date = Cast(
        F('land_date') - Cast(Value('3 months'), DurationField()),
        DateField(),
    )
    year = ExtractYear(adjusted_land_date)
    financial_year = Concat(
        Cast(year, CharField()),
        Value('/'),
        Cast(year + 1, CharField()),
    )
    return Case(When(land_date=None, then=Value('')), default=financial_year)


def get_country_url():
    """
    Gets an SQL expression that returns a Data Hub front-end URL for a country
    with applied filters.
    """
    key = 'mi_fdi_dashboard_country'
    country_url = Concat(
        Value(f'{settings.DATAHUB_FRONTEND_URL_PREFIXES[key]}'),
        Cast('investor_company__address_country__id', CharField()),
    )
    return Case(
        When(
            investor_company__address_country=None,
            then=Value(''),
        ),
        default=country_url,
    )
