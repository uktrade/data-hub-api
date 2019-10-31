from datahub.core.query_utils import get_string_agg_subquery
from datahub.investment.project.models import InvestmentProject


def get_investment_project_to_many_string_agg_subquery(expression):
    """
    Returns a subquery that uses string_agg to concatenate values of a to-many field
    of investment project
    """
    return get_string_agg_subquery(
        InvestmentProject,
        expression,
    )
