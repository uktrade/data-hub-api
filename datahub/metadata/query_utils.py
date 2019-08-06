from django.db.models import F, Func, OuterRef, Subquery, TextField, Value

from datahub.metadata.models import Sector, Service


class _StringAgg(Func):
    function = 'STRING_AGG'
    template = '%(function)s(%(expressions)s ORDER BY "lft")'


def _get_name_from_mptt_model(model, relation_name=None):
    """
    Generates a subquery that can be used to add mptt model names to a query set as an annotation.

    The generated SQL expression for the column (in the first example) will be similar to:

        SELECT STRING_AGG(U0."segment", ' : ' ORDER BY "lft") AS "name"
        FROM "<model>" U0
        WHERE (
            U0."lft" <= ("<model>"."lft")
            AND U0."rght" >= ("<model>"."rght")
            AND U0."tree_id" = ("<model>."tree_id")
        )

    (Refer to the django-mptt documentation for information on what the lft, rght and tree_id
    columns mean.)
    """
    outer_ref_prefix = f'{relation_name}__' if relation_name is not None else ''

    subquery = model.objects.annotate(
        name=_StringAgg(F('segment'), Value(model.PATH_SEPARATOR)),
    ).filter(
        lft__lte=OuterRef(f'{outer_ref_prefix}lft'),
        rght__gte=OuterRef(f'{outer_ref_prefix}rght'),
        tree_id=OuterRef(f'{outer_ref_prefix}tree_id'),
    ).order_by().values('name')

    return Subquery(subquery, output_field=TextField())


def get_sector_name_subquery(relation_name=None):
    """
    Generates a subquery that can be used to add sector names to a query set as an annotation.

    Usage examples:

        Sector.objects.annotate(name=get_sector_name_subquery())
        Company.objects.annotate(sector_name=get_sector_name_subquery('sector'))

    """
    return _get_name_from_mptt_model(Sector, relation_name)


def get_service_name_subquery(relation_name=None):
    """
    Generates a subquery that can be used to add service names to a query set as an annotation.

    Usage examples:

        Service.objects.annotate(name=get_service_name_subquery())
    """
    return _get_name_from_mptt_model(Service, relation_name)
