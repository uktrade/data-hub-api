from django.db.models import Func, TextField, Value
from django.db.models.functions import Coalesce, Concat


def get_project_code_expression():
    """Gets an SQL expression that returns the formatted project code for an investment project."""
    return Coalesce(
        'cdms_project_code',
        Concat(
            Value('DHP-'),
            Func('investmentprojectcode', Value('fm00000000'), function='to_char'),
        ),
        output_field=TextField(),
    )
