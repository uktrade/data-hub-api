from datahub.core.validate_utils import DataCombiner
from datahub.investment.validate import field_incomplete


def get_incomplete_fields(instance, fields, model):
    """Returns a list of fields that are incomplete."""
    combiner = DataCombiner(instance, {}, model=model)
    incomplete_fields = []
    for field in fields:
        if field_incomplete(combiner, field):
            incomplete_fields.append(field)
    return incomplete_fields
