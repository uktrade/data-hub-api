from secrets import token_urlsafe

from django.db.models import Exists, OuterRef
from django.db.models.deletion import CASCADE, get_candidate_relations_to_delete


def get_related_fields(model):
    """
    Returns all the fields of `model` that hold the link between referencing objects
    and the referenced object (`model`).

    :param model: orphaned model class
    :returns: list of fields of `model` that hold references via dependent objects
    """
    return [
        f for f in model._meta.get_fields(include_hidden=True)
        if (f.one_to_many or f.one_to_one or f.many_to_many or f.many_to_one)
        and f.auto_created
        and not f.concrete
        and not f.field.model._meta.auto_created
    ]


def get_unreferenced_objects_query(model):
    """
    :param model: orphaned model class
    :returns: queryset for unreferenced objects
    """
    fields = get_related_fields(model)

    identifiers = [f'ann_{token_urlsafe(6)}' for _ in range(len(fields))]

    qs = model.objects.all()
    for identifier, field in zip(identifiers, fields):
        related_field = field.field
        subquery = related_field.model.objects.filter(
            **{related_field.attname: OuterRef('pk')},
        ).only('pk')
        qs = qs.annotate(**{identifier: Exists(subquery)})

    filter_args = {identifier: False for identifier in identifiers}

    return qs.filter(**filter_args)


def get_relations_to_delete(model):
    """
    Returns all the fields of `model` that point to models which would get deleted
    (on cascade) as a result this model getting deleted.

    :param model: model class
    :returns: list of fields of `model` that point to models deleted in cascade
    """
    candidates = get_candidate_relations_to_delete(model._meta)
    return [
        field for field in candidates
        if field.field.remote_field.on_delete == CASCADE
    ]
