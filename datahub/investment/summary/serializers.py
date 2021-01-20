from django.db.models import Case, Count, F, Q, When
from django.db.models.functions import Coalesce, Extract
from django.utils import timezone
from rest_framework import serializers

from datahub.company.models import Advisor
from datahub.core.constants import InvestmentProjectStage
from datahub.core.utils import get_financial_year
from datahub.investment.project.models import InvestmentProject


class AdvisorIProjectSummarySerializer(serializers.Serializer):
    """
    Serializer for Investment Project Summaries.
    """

    annual_summaries = serializers.SerializerMethodField(read_only=True)
    adviser_id = serializers.UUIDField(source='id')

    class Meta:
        model = Advisor

    def get_annual_summaries(self, obj):
        """
        Gets annual summaries for the current and previous financial years.
        """
        current_financial_year = get_financial_year(timezone.now())
        start_year = current_financial_year - 1
        end_year = current_financial_year + 1

        # Get any projects where this adviser is involved
        projects = InvestmentProject.objects.filter(
            Q(client_relationship_manager__id=obj.id)
            | Q(project_assurance_adviser__id=obj.id)
            | Q(project_manager__id=obj.id)
            | Q(team_members__id=obj.id),
        )

        prospect_count = projects.filter(
            stage=InvestmentProjectStage.prospect.value.id,
        ).count()

        project_summaries = (
            projects.annotate(
                land_date=Coalesce('actual_land_date', 'estimated_land_date'),
                land_date_year=Extract('land_date', 'year'),
                land_date_month=Extract('land_date', 'month'),
                financial_year=Case(
                    When(land_date_month__gt=4, then=F('land_date_year')),
                    default=F('land_date_year') - 1,
                ),
            )
            .exclude(stage=InvestmentProjectStage.prospect.value.id)
            .filter(financial_year__gte=start_year - 1, financial_year__lt=end_year)
            .values('financial_year', 'stage', 'stage__name')
            .annotate(count=Count('stage'))
            .order_by('financial_year')
        )

        results = {}
        for financial_year in range(start_year, end_year):
            results[financial_year] = {
                'financial_year': f'{financial_year}-{str(financial_year + 1)[-2:]}',
                'totals': {
                    'prospect': prospect_count,
                    'assign_pm': 0,
                    'active': 0,
                    'verify_win': 0,
                    'won': 0,
                },
            }

        for project_summary in project_summaries:
            year = project_summary['financial_year']
            stage = InvestmentProjectStage.get_by_id(project_summary['stage'])
            stage_name = None if stage is None else stage.name
            results[year]['totals'][stage_name] = project_summary['count']

        return list(results.values())
