

def model_to_dict(model_instance):
    """Transform a model to a dict.

    FK are represented as related object pk as string
    M2M are represented as lists of related objects pks (as strings)
    """
    options = model_instance._meta
    data = {}
    for field in options.concrete_fields:
        data[field.name] = field.value_from_object(model_instance)
    for field in options.many_to_many:
        if model_instance.pk is None:
            data[field.name] = []
        else:
            data[field.name] = list(field.value_from_object(model_instance).values_list('pk', flat=True))
    return data


def queryset_to_list_of_dicts(queryset):
    """Transform queryset to a list of dicts."""
    return [model_to_dict(instance) for instance in queryset]
