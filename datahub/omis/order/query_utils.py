from django.db.models import CharField, OuterRef, Subquery

from datahub.core.query_utils import get_full_name_expression
from datahub.omis.order.models import OrderAssignee


def get_lead_order_assignee_name_subquery():
    """Get lead order assignee name subquery."""
    subquery = OrderAssignee.objects.filter(
        order=OuterRef('pk'),
        is_lead=True,
    ).annotate(
        name=get_full_name_expression('adviser'),
    ).values(
        'name',
    )
    return Subquery(subquery, output_field=CharField())
