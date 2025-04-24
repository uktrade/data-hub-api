from django_filters import rest_framework as filters
from django_filters.widgets import CSVWidget
from rest_framework.exceptions import ValidationError

from datahub.company_activity.models import KingsAwardRecipient


class KingsAwardRecipientFilterSet(filters.FilterSet):
    """Kings Award Recipient filter set."""

    year_awarded = filters.BaseInFilter(
        field_name='year_awarded',
        widget=CSVWidget,
        lookup_expr='in',
    )
    category = filters.CharFilter(method='filter_category')

    class Meta:
        model = KingsAwardRecipient
        fields = ['year_awarded', 'category']

    def filter_category(self, queryset, name, value):
        """Filters queryset by category alias."""
        aliases = [alias.strip() for alias in value.split(',') if alias.strip()]
        if not aliases:
            return queryset

        category_values = []
        invalid_aliases = []
        for alias in aliases:
            try:
                category_values.append(KingsAwardRecipient.Category.from_alias(alias))
            except ValueError:
                invalid_aliases.append(alias)

        if invalid_aliases:
            raise ValidationError(
                f'Invalid category alias(es): {", ".join(invalid_aliases)}. '
                f'Valid aliases are: {", ".join(KingsAwardRecipient.Category.alias_mapping.keys())}.',
            )

        return queryset.filter(category__in=category_values)
