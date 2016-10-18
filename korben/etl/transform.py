'''
Functions for transforming dicts from Django to OData shape and back again,
according to spec.MAPPINGS
'''
from . import spec


def django_to_odata(django_tablename, django_dict):
    '''
    Transform a Django dict to an OData dict

    Returns a tuple (etag: bool, odata_dict: dict) where the bool shows whether
    the OData entity has ETag requirements and the dict is the passed
    django_dict transformed according to the spec in etl.specs.MAPPINGS
    '''
    odata_dict = {}
    mapping = spec.MAPPINGS[spec.DJANGO_LOOKUP[django_tablename]]
    for odata_col, django_col in mapping.get('local', ()):
        value = django_dict.get(django_col)
        if odata_col and value:
            odata_dict[odata_col] = value
    for odata_prefix, field_map in mapping.get('nonflat', ()):
        unflattened = {}
        for odata_suffix, django_col in field_map:
            value = django_dict.get(django_col)
            if not value:
                continue
            unflattened[odata_suffix] = value
        if not unflattened:
            continue
        odata_dict[odata_prefix] = unflattened
    return mapping.get('etag', False), odata_dict


def odata_to_django(odata_tablename, odata_dict):
    'Transform an OData dict to a Django dict'
    django_dict = {}
    mapping = spec.MAPPINGS[odata_tablename]
    for odata_col, django_col in mapping.get('local', ()):
        value = odata_dict.get(odata_col)
        if odata_col:
            django_dict[django_col] = value
    for odata_prefix, field_map in mapping.get('nonflat', ()):
        prefix_dict = odata_dict.get(odata_prefix)
        if not prefix_dict:
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
    for django_col in mapping.get('empty_strings', ()):
        django_dict[django_col] = django_dict.get(django_col) or ''
    for django_col in mapping.get('use_undefined', ()):
        django_dict[django_col] =\
            django_dict.get(django_col) or spec.CONSTANT_UNDEFINED_ID
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
