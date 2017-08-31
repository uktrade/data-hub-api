def generate_reference(model, gen, field='reference', prefix='', max_retries=10):
    """
    Generate a unique reference given:

    :param model: the class of the django model
    :param gen: a function without arguments that returns part or all the reference
    :param field: reference field of the model that needs to be unique
    :param prefix: optional prefix
    :param max_retries: max number of retries before failing

    :raises RuntimeError: after trying max_retries times without being able to generate a
        valid value
    """
    manager = model.objects
    for _ in range(max_retries):
        reference = f'{prefix}{gen()}'
        if not manager.filter(**{field: reference}).exists():
            return reference

    raise RuntimeError('Cannot generate random reference')
