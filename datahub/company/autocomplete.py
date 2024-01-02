from django.db.models import Exists, OuterRef
from datahub.core.autocomplete import _apply_autocomplete_filter_to_queryset, AutocompleteFilter
from datahub.user.company_list.models import CompanyListItem


class WithListAutocompleteFilter(AutocompleteFilter):
    """
    Autocomplete function that prepends any companies from the current users' list to the results.
    """

    def filter(self, queryset, value):
        """Filters the queryset."""
        # This gets called even if the query parameter is not in the query string. So do nothing
        # if the query string was not specified
        if self.field_name not in self.parent.form.data:
            return queryset

        adviser = self.parent.request.user

        queryset = queryset.annotate(
            is_in_adviser_list=Exists(
                CompanyListItem.objects.filter(company=OuterRef('pk'), list__adviser=adviser)
            )
        )

        return _apply_autocomplete_filter_to_queryset(
            queryset,
            self.search_fields,
            value,
            priority_order_by=['-is_in_adviser_list'],
        )
