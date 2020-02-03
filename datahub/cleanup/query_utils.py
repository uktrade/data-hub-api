from django.db.models import Exists, OuterRef, Q
from django.db.models.deletion import CASCADE, get_candidate_relations_to_delete

from datahub.core.model_helpers import get_related_fields


def get_unreferenced_objects_query(
    model,
    excluded_relations=(),
    relation_exclusion_filter_mapping=None,
):
    """
    Generates a query set of unreferenced objects for a model.

    :param model: the model to generate a query set of unreferenced objects
    :param excluded_relations: related fields on model that should be ignored
    :param relation_exclusion_filter_mapping:
        Optional mapping of relations (fields on model) to Q objects.
        For each relation where a Q object is provided, the Q object is used to exclude
        objects for that relation prior to checking if any references to the model exist (for
        that relation).

        Example:
            This example will not consider interactions dated before 2015-01-01 when getting
            unreferenced companies.

            get_unreferenced_objects_query(
                Company,
                relation_exclusion_filter_mapping={
                    Company._meta.get_field('interactions'): Q(date__lt=date(2015, 1, 1),
                }
            )

    :returns: queryset for unreferenced objects

    """
    if relation_exclusion_filter_mapping is None:
        relation_exclusion_filter_mapping = {}

    fields = set(get_related_fields(model)) - set(excluded_relations)

    if relation_exclusion_filter_mapping.keys() - fields:
        raise ValueError('Invalid fields detected in relation_exclusion_filter_mapping.')

    q = Q()

    for field in fields:
        related_field = field.field
        exclusion_filters = relation_exclusion_filter_mapping.get(field, Q())
        subquery = related_field.model.objects.filter(
            **{related_field.attname: OuterRef('pk')},
        ).exclude(
            exclusion_filters,
        ).only('pk')
        q &= Q(~Exists(subquery))

    return model.objects.filter(q)


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
