# from django_filters import CharFilter
from django.db.models import BooleanField, IntegerField, Case, Count, F, Value, When, Q, Exists

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
        # adviser = Adviser.objects.get(pk='6e786ddd-1f57-4b38-a3fe-04092194382a')
        adviser = Adviser.objects.get(pk='80ecf4f4-82f0-45d0-b6f1-913b1d27293d')
        from pprint import pprint

        # pprint("queryset")
        # pprint(queryset)

        result = queryset.annotate(
            in_adviser_list_count=Count('company_list_items', output_field=IntegerField()),
        )

        result = result.annotate(
            in_adviser_list=Case(
                When(
                    Q(company_list_items__list__adviser=adviser),
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )

        result = _apply_autocomplete_filter_to_queryset(
            result, self.search_fields, value, priority_order_by=['-in_adviser_list']
        )
        # result.order_fields('in_adviser_list')
        pprint("result.query.order_by")
        pprint(result.order_by)
        # order_by = result.order_by

        # result.order_by(
        #     'in_adviser_list',
        #     order_by,
        # )
        # result.order_by.prepend('in_adviser_list')

        # for query in queryset:
        #     pprint("query.company_list_items")
        #     pprint(query.company_list_items.all())

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
        # pprint("str(result.query)")
        # pprint(str(result.query))
        return result
