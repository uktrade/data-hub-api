from datahub.core.validate_utils import is_not_blank


def remove_blank_from_dict(data):
    """Optimise data from default outputted dictionary"""
    if isinstance(data, dict):
        return dict(
            (key, remove_blank_from_dict(value))
            for key, value in data.items()
            if is_not_blank(value) and is_not_blank(remove_blank_from_dict(value))
        )
    if isinstance(data, list):
        return [
            remove_blank_from_dict(value)
            for value in data
            if is_not_blank(value) and is_not_blank(remove_blank_from_dict(value))
        ]
    return data
