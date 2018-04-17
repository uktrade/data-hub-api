class Echo:
    """Represents dummy writer."""

    def write(self, value):
        """Returns value that is being "written"."""
        return value


def get_model_fields(es_model):
    """Gets the field objects for an ES model."""
    return es_model._doc_type.mapping.properties._params['properties']


def get_model_field_names(es_model):
    """Gets the field names for an ES model."""
    return get_model_fields(es_model).keys()


def get_model_copy_to_target_field_names(es_model):
    """Gets the names of fields (for an ES model) that are copy-to targets."""
    fields = get_model_fields(es_model)

    copy_to_field_lists = [
        [prop.copy_to] if isinstance(prop.copy_to, str) else prop.copy_to
        for prop in fields.values()
        if hasattr(prop, 'copy_to')
    ]

    return {field for fields in copy_to_field_lists for field in fields}


def get_model_non_mapped_field_names(es_model):
    """Gets the names of fields that are not copied to, mapped or computed."""
    return (
        get_model_field_names(es_model)
        - get_model_copy_to_target_field_names(es_model)
        - es_model.MAPPINGS.keys()
        - es_model.COMPUTED_MAPPINGS.keys()
    )
