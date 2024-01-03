from datahub.core.viewsets import CoreViewSet
from datahub.export_win.models import Win
from datahub.export_win.serializers import WinSerializer


class WinViewSet(CoreViewSet):
    """Views for Export wins."""

    serializer_class = WinSerializer
    queryset = Win.objects.select_related(
        'customer_location',
        'type',
        'country',
        'goods_vs_services',
        'sector',
        'hvc',
        'hvo_programme',
        'lead_officer',
        'line_manager',
        'team_type',
        'hq_team',
        'business_potential',
        'export_experience',
    ).prefetch_related(
        'type_of_support',
        'associated_programme',
        'team_members',
        'advisers',
    )
