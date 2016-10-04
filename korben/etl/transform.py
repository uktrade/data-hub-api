from . import spec


def django_to_odata(django_table, django_dict):
    'Transform a Django dict to an OData dict'
    odata_dict = {}
    mapping = spec.MAPPINGS[spec.DJANGO_LOOKUP[django_table.name]]
    for odata_col, django_col in mapping.get('local', []):
        if odata_col:
            odata_dict[odata_col] = django_dict[django_col]
    return odata_dict


def odata_to_django(table, odata_dict):
    'Transform an OData dict to a Django dict'
    django_dict = {}
    mapping = spec.MAPPINGS[table.name]
    for odata_col, django_col in mapping.get('local', []):
        if odata_col:
            django_dict[django_col] = odata_dict[odata_col]
    return django_dict
