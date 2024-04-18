from datahub.dbmaintenance.utils import parse_date


def filter_data_by_modified_date(updated_since, queryset):
    if updated_since:
        updated_since_date = parse_date(updated_since)
        if updated_since_date:
            queryset = queryset.filter(modified_on__gt=updated_since_date)
    return queryset
