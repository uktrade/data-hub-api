from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import Case, F, Func, OuterRef, Subquery, Value, When
from django.db.models.functions import Concat, NullIf


class ConcatWS(Func):
    """
    Concatenates text fields together with a separator.

    The first argument is the separator. Null arguments are ignored.

    Usage example:
        ConcatWS(Value(' '), 'first_name', 'last_name')
    """

    function = 'concat_ws'


class PreferNullConcat(Func):
    """
    Concatenates a sequence of expressions, but evaluates to NULL if any one expression does
    (in PostgreSQL).
    """

    template = '%(expressions)s'
    arg_joiner = ' || '


def get_string_agg_subquery(model, expression, delimiter=', '):
    """
    Gets a subquery that uses string_agg to concatenate values in a to-many field.

    The passed model must be the model of the query set being annotated.

    At present values are concatenated in an undefined order, however Django 2.2 added support for
    providing an ordering.

    TODO: However, the StringAgg ordering keyword argument is not currently used due to the
     problem described in https://code.djangoproject.com/ticket/30315.

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


def get_top_related_expression_subquery(related_field, expression, ordering):
    """
    Returns an expression that gets a particular field of the top row for a particular ordering
    of a related model.

    expression could be a string referring to a field, or an instance of Expression.

    Usage example:
        Company.objects.annotate(
            team_of_latest_interaction=get_top_related_expression_subquery(
                Interaction.investment_project.field,
                'dit_team__name',
                ('-date',),
            ),
        )
    """
    wrapped_expression = F(expression) if isinstance(expression, str) else expression
    queryset = related_field.model.objects.annotate(
        _annotated_value=wrapped_expression,
    ).filter(
        **{related_field.name: OuterRef('pk')},
    ).order_by(
        *ordering,
    ).values(
        '_annotated_value',
    )[:1]

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


def get_full_name_expression(person_field_name=None, bracketed_field_name=None):
    """
    Gets an SQL expression that returns the full name for a contact or adviser.

    Can both be used directly on a Contact or Adviser query set and on related fields.

    Usage examples:

        # Effectively '{Contact.first_name} {Contact.last_name}'
        Contact.objects.annotate(
            name=get_full_name_expression(),
        )

        # Effectively '{Contact.first_name} {Contact.last_name} ({Contact.job_title})'
        # (but the job title would be omitted if blank or NULL)
        Contact.objects.annotate(
            name=get_full_name_expression(bracketed_field_name='job_title'),
        )

        # Effectively '{Interaction.dit_adviser.first_name} {Interaction.dit_adviser.last_name}'
        Interaction.objects.annotate(
            dit_adviser_name=get_full_name_expression(person_field_name='dit_adviser'),
        )
    """
    if person_field_name is None:
        return _full_name_concat(
            'first_name',
            'last_name',
            bracketed_field=bracketed_field_name,
        )

    evaluated_bracketed_field_name = (
        f'{person_field_name}__{bracketed_field_name}' if bracketed_field_name else None
    )

    return Case(
        When(
            **{f'{person_field_name}__isnull': False},
            then=_full_name_concat(
                f'{person_field_name}__first_name',
                f'{person_field_name}__last_name',
                bracketed_field=evaluated_bracketed_field_name,
            ),
        ),
        default=None,
    )


def _full_name_concat(first_name_field, last_name_field, bracketed_field=None):
    parts = [
        NullIf(first_name_field, Value('')),
        NullIf(last_name_field, Value('')),
    ]

    if bracketed_field:
        bracketed_expression = PreferNullConcat(
            Value('('),
            NullIf(bracketed_field, Value('')),
            Value(')'),
        )
        parts.append(bracketed_expression)

    return ConcatWS(Value(' '), *parts)


def get_front_end_url_expression(model_name, pk_expression, url_suffix=''):
    """
    Gets an SQL expression that returns a front-end URL for an object.

    :param model_name:      key in settings.DATAHUB_FRONTEND_URL_PREFIXES
    :param pk_expression:   expression that resolves to the pk for the model
    :param url_suffix:      Optional: string appended to the end of the url
    """
    return Concat(
        Value(f'{settings.DATAHUB_FRONTEND_URL_PREFIXES[model_name]}/'),
        pk_expression,
        Value(url_suffix),
    )
