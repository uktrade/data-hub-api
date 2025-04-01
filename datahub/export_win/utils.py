from django.db.models import Sum

from datahub.core import constants


def calculate_totals_for_export_win(win_instance):
    """Base class for Total Export, Non Export and ODI."""
    export_type_value = constants.BreakdownType.export.value
    non_export_value = constants.BreakdownType.non_export.value
    odi_value = constants.BreakdownType.odi.value
    return {
        'total_export_value': win_instance.breakdowns.filter(
            type_id=export_type_value.id,
        ).aggregate(
            total_export_value=Sum('value'),
        )['total_export_value']
        or 0,
        'total_non_export_value': win_instance.breakdowns.filter(
            type_id=non_export_value.id,
        ).aggregate(
            total_non_export_value=Sum('value'),
        )['total_non_export_value']
        or 0,
        'total_odi_value': win_instance.breakdowns.filter(type_id=odi_value.id).aggregate(
            total_odi_value=Sum('value'),
        )['total_odi_value']
        or 0,
    }
