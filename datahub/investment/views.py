from datahub.core.viewsets import CoreViewSetV3
from datahub.investment.models import InvestmentProject
from datahub.investment.serializers import (
    IProjectRequirementsSerializer, IProjectSerializer, IProjectTeamSerializer,
    IProjectValueSerializer
)


class IProjectViewSet(CoreViewSetV3):
    """Investment project views.

    This is a subset of the fields on an InvestmentProject object.
    """

    read_serializer_class = IProjectSerializer
    write_serializer_class = IProjectSerializer
    queryset = InvestmentProject.objects.select_related(
        'investment_type',
        'phase',
        'investor_company',
        'intermediate_company',
        'investment_recipient_company',
        'client_relationship_manager',
        'referral_source_advisor',
        'referral_source_activity',
        'referral_source_activity_website',
        'referral_source_activity_marketing',
        'referral_source_activity_event',
        'fdi_type',
        'non_fdi_type',
        'sector'
    ).prefetch_related(
        'client_contacts',
        'business_activity'
    )


class IProjectValueViewSet(CoreViewSetV3):
    """Investment project value views.

    This is a subset of the fields on an InvestmentProject object.
    """

    read_serializer_class = IProjectValueSerializer
    write_serializer_class = IProjectValueSerializer
    queryset = InvestmentProject.objects.select_related('average_salary')


class IProjectRequirementsViewSet(CoreViewSetV3):
    """Investment project requirements views.

    This is a subset of the fields on an InvestmentProject object.
    """

    read_serializer_class = IProjectRequirementsSerializer
    write_serializer_class = IProjectRequirementsSerializer
    queryset = InvestmentProject.objects.prefetch_related(
        'competitor_countries',
        'uk_region_locations',
        'strategic_drivers'
    )


class IProjectTeamViewSet(CoreViewSetV3):
    """Investment project team views.

    This is a subset of the fields on an InvestmentProject object.
    """

    read_serializer_class = IProjectTeamSerializer
    write_serializer_class = IProjectTeamSerializer
    queryset = InvestmentProject.objects.select_related(
        'project_manager',
        'project_manager__dit_team',
        'project_assurance_advisor',
        'project_assurance_advisor__dit_team'
    )
