from django.db.models import F

from datahub.company.models import Company
from datahub.core.query_utils import get_top_related_expression_subquery
from datahub.interaction.models import Interaction


def get_company_queryset():
    """
    Returns an annotated query set used by DNBCompanySearchView.

    The annotations are supported by an index on the Interaction model.

    (Note that getting all four interaction fields in one expression currently is not easily
    done with the Django ORM, hence four annotations are used.)
    """
    return Company.objects.annotate(
        latest_interaction_id=_get_field_of_latest_interaction('pk'),
        latest_interaction_created_on=_get_field_of_latest_interaction('created_on'),
        latest_interaction_date=_get_field_of_latest_interaction('date'),
        latest_interaction_subject=_get_field_of_latest_interaction('subject'),
    )


def _get_field_of_latest_interaction(field):
    return get_top_related_expression_subquery(
        Interaction.company.field,
        F(field),
        ('-date', '-created_on', 'pk'),
        outer_field='id',
    )
