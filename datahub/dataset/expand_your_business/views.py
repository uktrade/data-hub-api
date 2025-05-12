from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q

from datahub.dataset.core.views import BaseFilterDatasetView
from datahub.dataset.expand_your_business.pagination import EYBDatasetViewCursorPagination
from datahub.investment_lead.models import EYBLead


class EYBLeadsDatasetView(BaseFilterDatasetView):
    """A GET API view to return the data for EYB leads."""

    pagination_class = EYBDatasetViewCursorPagination

    def get_dataset(self, request):
        """Returns queryset of EYB lead records."""
        return (
            EYBLead.objects.select_related(
                'sector',
                'proposed_investment_region',
            )
            .annotate(
                investment_project_ids=ArrayAgg(
                    'investment_projects__id',
                    ordering=[
                        'investment_projects__name',
                        'investment_projects__id',
                    ],
                    filter=Q(investment_projects__isnull=False),
                    default=[],
                ),
            )
            .values(
                'id',
                'modified_on',
                # Triage component
                'triage_hashed_uuid',
                'triage_created',
                'triage_modified',
                'sector',
                'sector_segments',
                'intent',
                'intent_other',
                'proposed_investment_region',
                'proposed_investment_city',
                'proposed_investment_location_none',
                'hiring',
                'spend',
                'spend_other',
                'is_high_value',
                # User component
                'user_hashed_uuid',
                'user_created',
                'user_modified',
                'company_name',
                'duns_number',
                'address_1',
                'address_2',
                'address_town',
                'address_county',
                'address_country',
                'address_postcode',
                'company_website',
                'full_name',
                'role',
                'email',
                'telephone_number',
                'agree_terms',
                'agree_info_email',
                'landing_timeframe',
                'company',
                'investment_project_ids',
                # Marketing component
                'marketing_hashed_uuid',
                'utm_name',
                'utm_source',
                'utm_medium',
                'utm_content',
            )
        )
