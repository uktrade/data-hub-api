from datahub.investment.project.models import InvestmentProject


def get_slim_investment_project_queryset():
    """Gets the nested investment query set for use in non-investment views (e.g. company)."""
    return InvestmentProject.objects.select_related(
        'investmentprojectcode',
    )
