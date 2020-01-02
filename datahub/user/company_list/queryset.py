from django.db.models import Case, DurationField, ExpressionWrapper, F, Q, When
from django.db.models.functions import Now

from datahub.core.query_utils import (
    get_array_agg_subquery,
    get_full_name_expression,
    get_top_related_expression_subquery,
    JSONBBuildObject,
)
from datahub.interaction.models import Interaction, InteractionDITParticipant
from datahub.user.company_list.models import CompanyListItem


def get_company_list_item_queryset():
    """
    Returns an annotated query set used by CompanyListItemViewSet and CompanyListViewSet.

    The annotations are supported by an index on the Interaction model.

    (Note that getting all three interaction fields in one expression currently is not easily
    done with the Django ORM, hence three annotations are used.)
    """
    return CompanyListItem.objects.annotate(
        latest_interaction_id=_get_field_of_latest_interaction('pk'),
        latest_interaction_created_on=_get_field_of_latest_interaction('created_on'),
        latest_interaction_date=_get_field_of_latest_interaction('date'),
        latest_interaction_subject=_get_field_of_latest_interaction('subject'),
        latest_interaction_dit_participants=_get_field_of_latest_interaction(
            get_array_agg_subquery(
                InteractionDITParticipant,
                'interaction',
                JSONBBuildObject(
                    adviser=_get_null_when_expression(
                        JSONBBuildObject(
                            id='adviser__id',
                            name=get_full_name_expression('adviser'),
                        ),
                        Q(adviser__isnull=True),
                    ),
                    team=_get_null_when_expression(
                        JSONBBuildObject(
                            id='team__id',
                            name='team__name',
                        ),
                        Q(team__isnull=True),
                    ),
                ),
                ordering=('pk',),
            ),
        ),
        latest_interaction_time_ago=ExpressionWrapper(
            Now() - F('latest_interaction_date'),
            output_field=DurationField(),
        ),
    ).select_related(
        'company',
    )


def _get_field_of_latest_interaction(field):
    return get_top_related_expression_subquery(
        Interaction.company.field,
        field,
        ('-date', '-created_on', 'pk'),
        outer_field='company_id',
    )


def _get_null_when_expression(expression, null_when_condition):
    return Case(
        When(
            null_when_condition,
            then=None,
        ),
        default=expression,
    )
