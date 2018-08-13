from django.db.models import F, Func, OuterRef, Subquery, TextField, Value

from datahub.metadata.models import Sector


class _SectorStringAgg(Func):
    function = 'STRING_AGG'
    template = '%(function)s(%(expressions)s ORDER BY "lft")'


def get_sector_name_subquery(relation_name=None):
    """
    Generates a subquery that can be used to add sector names to a query set as an annotation.

    Usage examples:

        Sector.objects.annotate(name=get_sector_name_subquery())
        Company.objects.annotate(sector_name=get_sector_name_subquery('sector'))

    The generated SQL expression for the column (in the first example) will be similar to:

        SELECT STRING_AGG(U0."segment", ' : ' ORDER BY "lft") AS "name"
        FROM "metadata_sector" U0
        WHERE (
            U0."lft" <= ("metadata_sector"."lft")
            AND U0."rght" >= ("metadata_sector"."rght")
            AND U0."tree_id" = ("metadata_sector"."tree_id")
        )

    (Refer to the django-mptt documentation for information on what the lft, rght and tree_id
    columns mean.)

    (The base manager is used here to avoid the default ordering being added to the query.)
    """
    outer_ref_prefix = f'{relation_name}__' if relation_name is not None else ''

    subquery = Sector._base_manager.annotate(
        name=_SectorStringAgg(F('segment'), Value(Sector.PATH_SEPARATOR))
    ).filter(
        lft__lte=OuterRef(f'{outer_ref_prefix}lft'),
        rght__gte=OuterRef(f'{outer_ref_prefix}rght'),
        tree_id=OuterRef(f'{outer_ref_prefix}tree_id'),
    ).values('name')

    return Subquery(subquery, output_field=TextField())
