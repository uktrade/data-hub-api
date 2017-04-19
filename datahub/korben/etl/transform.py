'''
Functions for transforming dicts from Django to OData shape and back again,
according to spec.MAPPINGS
'''
import datetime
import functools

from korben.cdms_api.rest.utils import cdms_datetime_to_datetime

from . import spec

def odata_to_django(odata_tablename, odata_dict):
    'Transform an OData dict to a Django dict'
    django_dict = {}
    mapping = spec.MAPPINGS[odata_tablename]

    # Simplest mapping from “local” dict key to renamed “local” key
    for odata_col, django_col in mapping.get('local', ()):
        value = odata_dict.get(odata_col)
        if odata_col:
            django_dict[django_col] = value

    # Transform the fields containgin Dynamics-style datetime strings to ISO
    # standard datetime strings
    for odata_col, django_col in mapping.get('datetime', ()):
        value = odata_dict.get(odata_col)
        if odata_col and value:
            result = cdms_datetime_to_datetime(value)
            if isinstance(result, datetime.datetime):
                result = result.isoformat()
            django_dict[django_col] = result

    for odata_prefix, field_map in mapping.get('nonflat', ()):
        # eurgh has to work two ways; once for data from cdms once for data
        # from the odata database
        prefix_dict = odata_dict.get(odata_prefix)
        if not prefix_dict:
            for odata_suffix, django_col in field_map:
                value = odata_dict.get(
                    "{0}_{1}".format(odata_prefix, odata_suffix)
                )
                if value:
                    django_dict[django_col] = value
            continue
        for odata_suffix, django_col in field_map:
            value = prefix_dict.get(odata_suffix)
            if not value:
                continue
            django_dict[django_col] = value

    for odata_cols, django_col, func in mapping.get('local_fn', ()):
        args = []
        for odata_col in odata_cols:
            args.append(odata_dict[odata_col])
        django_dict[django_col] = func(*args)

    for django_col in mapping.get('use_undefined', ()):
        django_dict[django_col] =\
            django_dict.get(django_col) or spec.ENUM_UNDEFINED_ID

    for django_col, func in mapping.get('defaults', ()):
        django_dict[django_col] = django_dict.get(django_col) or func()

    for odata_cols, django_col, _ in mapping.get('concat', ()):
        value = functools.reduce(
            lambda acc, col: acc + (odata_dict[col] or ''), odata_cols, ''
        )
        django_dict[django_col] = value

    # call this last
    for django_col in mapping.get('empty_strings', ()):
        django_dict[django_col] = django_dict.get(django_col) or ''
    return django_dict


def colnames_shortlong(table_name, data_in):
    'Map from short column names to long column names'
    data_out = {}
    for col_short, value in data_in.items():
        col_long = spec.COLNAME_SHORTLONG.get((table_name, col_short))
        if col_long:
            data_out[col_long] = value
        else:
            data_out[col_short] = value
    return data_out


def colnames_longshort(table_name, data_in):
    'Map from long column names to short column names'
    data_out = {}
    for col_long, value in data_in.items():
        col_short = spec.COLNAME_LONGSHORT.get((table_name, col_long))
        if col_short:
            data_out[col_short] = value
        else:
            data_out[col_long] = value
    return data_out
