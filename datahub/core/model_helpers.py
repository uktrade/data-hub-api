"""
Contains various utilities and helper functions for working with models.

(This module is named model_helpers rather than model_utils as we were previously
using a third-party package called model_utils.)
"""


def get_m2m_model(model, field_name):
    """
    Gets the many-to-many through model for a many-to-many field.

    This is rarely needed, but can be useful in rare cases when a hidden many-to-many
    through model automatically created by Django needs to be accessed.
    """
    return model._meta.get_field(field_name).remote_field.through


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


def get_self_referential_relations(model):
    """
    Returns all fields of `model` that refer back to `model`.

    :param model: model class
    :returns: list of self-referential fields of `model`
    """
    return [
        f for f in model._meta.get_fields(include_hidden=True)
        if (f.one_to_many or f.one_to_one or f.many_to_many or f.many_to_one)
        and not f.auto_created
        and f.concrete
        and f.remote_field.model is model
    ]
