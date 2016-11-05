'''
Functions for transforming dicts from Django to OData shape and back again,
according to spec.MAPPINGS
'''
import functools
from . import spec
from korben.services import db
from korben.cdms_api.rest.utils import cdms_datetime_to_datetime
from korben.cdms_api.rest.utils import datetime_to_cdms_datetime



def django_to_odata(django_tablename, django_dict):
    '''
    Transform a Django dict to an OData dict

    Returns a tuple (etag: bool, odata_dict: dict) where the bool shows whether
    the OData entity has ETag requirements and the dict is the passed
    django_dict transformed according to the spec in etl.specs.MAPPINGS
    '''

    odata_dict = {}
    odata_tablename = spec.DJANGO_LOOKUP[django_tablename]
    mapping = spec.MAPPINGS[odata_tablename]

    for django_col in mapping.get('use_undefined', ()):
        if django_dict.get(django_col) == spec.ENUM_UNDEFINED_ID:
            del django_dict[django_col]

    for odata_col, django_col in mapping.get('local', ()):
        value = django_dict.get(django_col)
        if odata_col and value:
            odata_dict[odata_col] = value

    for odata_col, django_col in mapping.get('datetime', ()):
        value = django_dict.get(django_col)
        if odata_col and value:
            odata_dict[odata_col] = datetime_to_cdms_datetime(value)

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

    for odata_prefix, defaults in mapping.get('nonflat_defaults', ()):
        if odata_prefix not in odata_dict:
            continue
        # TODO: Make this less poor; it’s called defaults, but it overwrites :/
        odata_dict[odata_prefix].update(defaults)

    for _, django_col, odata_col in mapping.get('concat', ()):
        value = django_dict.get(django_col)
        if value:
            odata_dict[odata_col] = value

    # handle adding single permitted “organization” id “root business unit”
    # (see etl.spec module) where appropriate
    # TODO: write this somewhere into the spec
    odata_metadata = db.get_odata_metadata()
    odata_table = odata_metadata.tables[odata_tablename]
    if 'OrganizationId_Id' in odata_table.columns:
        odata_dict['OrganizationId'] = {
            'Id': spec.STAGING_ORGANIZATION_ID,
        }
    if 'OrganizationId' in odata_table.columns:
        odata_dict['OrganizationId'] = spec.STAGING_ORGANIZATION_ID
    if 'ParentBusinessUnitId_Id' in odata_table.columns:
        odata_dict['ParentBusinessUnitId'] = {
            'Id': spec.STAGING_ROOT_BUSINESSUNIT_ID,  # TODO: handle prod case
        }
    if 'BusinessUnitId_Id' in odata_table.columns:
        odata_dict['BusinessUnitId'] = {
            'Id': spec.STAGING_ROOT_BUSINESSUNIT_ID,  # TODO: handle prod case
        }

    return mapping.get('etag', False), odata_dict


def odata_to_django(odata_tablename, odata_dict):
    'Transform an OData dict to a Django dict'
    django_dict = {}
    mapping = spec.MAPPINGS[odata_tablename]

    for odata_col, django_col in mapping.get('local', ()):
        value = odata_dict.get(odata_col)
        if odata_col:
            django_dict[django_col] = value

    for odata_col, django_col in mapping.get('datetime', ()):
        value = odata_dict.get(odata_col)
        if odata_col and value:
            django_dict[django_col] =\
                cdms_datetime_to_datetime(value).isoformat()

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
