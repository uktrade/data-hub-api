from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Case, OuterRef, Subquery, Value, When
from django.db.models.functions import Concat


def get_string_agg_subquery(model, expression, delimiter=', '):
    """
    Gets a subquery that uses string_agg to concatenate values in a to-many field.

    The passed model must be the model of the query set being annotated.

    At present values are concatenated in an undefined order, however Django 2.2 adds support for
    providing an ordering.

    TODO: Add ordering when Django 2.2 is released.

    Usage example:
        Company.objects.annotate(
            export_to_country_names=get_string_agg_subquery(Company, 'export_to_countries__name'),
        )
    """
    return get_aggregate_subquery(model, StringAgg(expression, delimiter))


def get_aggregate_subquery(model, expression):
    """
    Gets a subquery that calculates an aggregate value of a to-many field.

    The passed model must be the model of the query set being annotated.

    Usage example:
        Company.objects.annotate(
            max_interaction_date=get_aggregate_subquery(
                Company,
                Max('interactions__date'),
            ),
        )
    """
    if not getattr(expression, 'contains_aggregate', False):
        raise ValueError('An aggregate expression must be provided.')

    queryset = model.objects.annotate(
        _annotated_value=expression,
    ).filter(
        pk=OuterRef('pk'),
    ).values(
        '_annotated_value',
    )

    return Subquery(queryset)


def get_choices_as_case_expression(model, field_name):
    """
    Gets an SQL expression that returns the display name for a field with choices.

    Usage example:
        InvestmentProject.objects.annotate(
            status_name=get_choices_as_case_expression(InvestmentProject, 'status'),
        )
    """
    field = model._meta.get_field(field_name)
    whens = (
        When(**{field.name: identifier}, then=Value(name)) for identifier, name in field.choices
    )
    return Case(*whens, default=field.name)


def get_full_name_expression(field_name):
    """
    Gets an SQL expression that returns the full name for a contact or adviser related field on
    another model.

    Usage example:
        Interaction.objects.annotate(
            dit_adviser_name=get_full_name_expression('dit_adviser'),
        )
    """
    return Case(
        When(
            **{f'{field_name}__isnull': False},
            then=Concat(f'{field_name}__first_name', Value(' '), f'{field_name}__last_name'),
        ),
        default=None,
    )


def get_front_end_url_expression(model_name, pk_expression):
    """
    Gets an SQL expression that returns a front-end URL for an object.

    :param model_name:      key in settings.DATAHUB_FRONTEND_URL_PREFIXES
    :param pk_expression:   expression that resolves to the pk for the model
    """
    return Concat(Value(f'{settings.DATAHUB_FRONTEND_URL_PREFIXES[model_name]}/'), pk_expression)
