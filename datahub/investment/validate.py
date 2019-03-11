

def field_incomplete(combiner, field):
    """Checks whether a field has been filled in."""
    if combiner.is_field_to_many(field):
        return not combiner.get_value_to_many(field)
    return combiner.get_value(field) in (None, '')
