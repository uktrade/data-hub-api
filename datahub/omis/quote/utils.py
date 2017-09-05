from pathlib import PurePath

from django.template.loader import render_to_string
from django.utils.crypto import get_random_string

from datahub.omis.core.utils import generate_reference


QUOTE_TEMPLATE = PurePath(__file__).parent / 'templates/content.md'


def generate_quote_reference(order):
    """
    :returns: a random unused reference of form:
            <order.reference>/Q-<(2) lettes>/<(1) number> e.g. GEA962/16/Q-AB1
    :raises RuntimeError: if no reference can be generated.
    """
    from .models import Quote

    def gen():
        return '{letters}{numbers}'.format(
            letters=get_random_string(length=2, allowed_chars='ACEFHJKMNPRTUVWXY'),
            numbers=get_random_string(length=1, allowed_chars='123456789')
        )
    return generate_reference(model=Quote, gen=gen, prefix=f'{order.reference}/Q-')


def generate_quote_content(order):
    """
    :returns: the content of the quote populated with the given order details.
    """
    return render_to_string(
        QUOTE_TEMPLATE,
        {'order': order}
    )
