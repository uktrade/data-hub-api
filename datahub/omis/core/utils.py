from datetime import datetime

from django.utils.timezone import now


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


def generate_datetime_based_reference(model, field='reference', prefix='', max_retries=10):
    """
    Generate a unique datetime based reference of type:
        <year><month><day><4-digit-seq> e.g. 201702300001

    :param model: the class of the django model
    :param field: reference field of the model that needs to be unique
    :param prefix: optional prefix
    :param max_retries: max number of retries before failing

    :raises RuntimeError: after trying max_retries times without being able to generate a
        valid value
    """
    current_date = now()
    dt_prefix = datetime.strftime(current_date, '%Y%m%d')

    def gen():
        # the select_for_update + len reduces race conditions (do not use .count()).
        # The problem could still occur when creating the first record of the day
        # but it's unlikely and if the transaction is atomic, it would not put
        # the db in an inconsistent state.
        start_count = len(
            model.objects.select_for_update().filter(created_on__date=current_date.date()),
        )

        while True:
            start_count += 1
            yield f'{start_count:04}'

    return generate_reference(
        model=model,
        gen=gen().__next__,
        prefix=f'{prefix}{dt_prefix}',
        field=field,
        max_retries=max_retries,
    )
