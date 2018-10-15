from enum import Enum
from itertools import islice
from logging import getLogger

import requests
from django.conf import settings

logger = getLogger(__name__)


class StrEnum(str, Enum):
    """
    Enum subclass where members are also str instances.

    Defined as per https://docs.python.org/3.6/library/enum.html#others
    """


class Echo:
    """
    Writer that echoes written data.

    Used for streaming large CSV files, defined as per
    https://docs.djangoproject.com/en/2.0/howto/outputting-csv/.
    """

    def write(self, value):
        """Returns value that is being "written"."""
        return value


class EchoUTF8:
    """
    Writer that echoes written data and encodes to utf-8 if necessary.

    Used for streaming large CSV files, defined as per
    https://docs.djangoproject.com/en/2.0/howto/outputting-csv/.
    """

    def write(self, value):
        """Returns value that is being "written"."""
        if isinstance(value, str):
            return value.encode('utf-8')
        return value


def join_truthy_strings(*args, sep=' '):
    """Joins a list of strings using a separtor, omitting falsey values."""
    return sep.join(filter(None, args))


def generate_enum_code_from_queryset(model_queryset):
    """Generate the Enum code for a given constant model queryset.

    Paste the generated text into the constants file.
    """
    for q in model_queryset:
        var_name = q.name.replace(' ', '_').lower()
        return f"{var_name} = Constant('{q.name}', '{q.id}')"


def stream_to_file_pointer(url, fp):
    """Efficiently stream given url to given file pointer."""
    response = requests.get(url, stream=True)
    for chunk in response.iter_content(chunk_size=4096):
        fp.write(chunk)


def slice_iterable_into_chunks(iterable, batch_size):
    """Collect data into fixed-length chunks or blocks."""
    iterator = iter(iterable)
    while True:
        batch_iter = islice(iterator, batch_size)
        objects = [row for row in batch_iter]
        if not objects:
            break
        yield objects


def load_constants_to_database(constants, model):
    """Loads an iterable of constants (typically an Enum) for a model to the database."""
    for constant in constants:
        model_obj, created = model.objects.get_or_create(pk=constant.value.id)
        if created or model_obj.name != constant.value.name:
            if created:
                logger.info('Creating %s "%s"', model._meta.verbose_name, constant.value.name)
            else:
                logger.info(
                    'Updating name of %s "%s" to "%s"',
                    model._meta.verbose_name,
                    model_obj.name,
                    constant.value.name,
                )

            model_obj.name = constant.value.name
            model_obj.save()


def get_front_end_url(obj):
    """Gets the URL for the object in the Data Hub internal front end."""
    url_prefix = settings.DATAHUB_FRONTEND_URL_PREFIXES[obj._meta.model_name]
    return f'{url_prefix}/{obj.pk}'
