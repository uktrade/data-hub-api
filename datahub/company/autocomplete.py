# from django_filters import CharFilter
from django.db.models import BooleanField, Case, Count, Value, When, Q, Exists

# from traitlets import Bool

from datahub.core.autocomplete import AutocompleteFilter, _apply_autocomplete_filter_to_queryset
from datahub.company.models.adviser import Advisor as Adviser


class WithListAutocompleteFilter(AutocompleteFilter):
    """
    Autocomplete function that prepends any companies from the current users' list to the results.
    """

    # def __init__(self, *args, search_fields=None, **kwargs):
    #     """
    #     Initialises the filter.

    #     The search_fields keyword argument specifies which fields to search and is required.
    #     """
    #     if search_fields is None:
    #         raise ValueError('The search_fields keyword argument must be specified')

    #     self.search_fields = search_fields
    #     super().__init__(*args, **kwargs)

    def filter(self, queryset, value):
        """Filters the queryset."""
        # This gets called even if the query parameter is not in the query string. So do nothing
        # if the query string was not specified
        if self.field_name not in self.parent.form.data:
            return queryset

        # adviser = request.user
        # Get current adviser
        # Limit list items to current adviser
        adviser = Adviser.objects.get(pk='6e786ddd-1f57-4b38-a3fe-04092194382a')
        from pprint import pprint

        # pprint("queryset")
        # pprint(queryset)

        result = _apply_autocomplete_filter_to_queryset(queryset, self.search_fields, value)

        queryset = queryset.annotate(
            in_adviser_list=Case(
                When(
                    Q(company_list_items=None),
                    then=Value(True),
                ),
                output_field=BooleanField(),
            ),
        )

        for query in queryset:
            pprint("query.company_list_items")
            pprint(query.company_list_items.all())

            # pprint("query.in_adviser_list")
            # pprint(query.in_adviser_list)

        # result.filter(company_list_items__list__adviser=adviser)
        # from pprint import pprint
        # pprint("result")
        # pprint(result._query.__dict__)
        # # queryset.filter['select_related'].append(company_list_item= {})
        # pprint("self.search_fields")
        # pprint(self.search_fields)
        # pprint("self")
        # pprint(self)
        # pprint("value")
        # pprint(value)
        return result
