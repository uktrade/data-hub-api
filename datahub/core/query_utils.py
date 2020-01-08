from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg, StringAgg
from django.contrib.postgres.fields import JSONField
from django.db.models import Case, CharField, F, Func, OuterRef, Subquery, Value, When
from django.db.models.functions import Coalesce, Concat, NullIf


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


class JSONBBuildObject(Func):
    """
    Create a JSONB field from keys and expressions.

    Can be used with subqueries to annotate a query with multiple values from the subquery at
    once.

    Usage example:

        Interaction.objects.annotate(
            contact_data=get_array_agg_subquery(
                Interaction.contacts.through,
                'interaction',
                JSONBBuildObject(first_name='first_name', last_name='last_name'),
            ),
        )
    """

    function = 'jsonb_build_object'
    output_field = JSONField()

    def __init__(self, **kwargs):
        """
        Initialise the function with a list of keys and expressions to build the JSON object
        from.
        """
        args = [
            expression
            for key, expression in kwargs.items()
            for expression in [Value(key), expression]
        ]
        super().__init__(*args)


def get_string_agg_subquery(model, expression, delimiter=', ', distinct=False):
    """
    Gets a subquery that uses string_agg to concatenate values in a to-many field.

    The passed model must be the model of the query set being annotated.

    Values are sorted alphabetically before concatenation.

    Usage example:
        Company.objects.annotate(
            export_to_country_names=get_string_agg_subquery(Company, 'export_to_countries__name'),
        )
    """
    return get_aggregate_subquery(
        model,
        StringAgg(expression, delimiter, ordering=(expression,), distinct=distinct),
    )


def get_array_agg_subquery(
    model,
    join_field_name,
    expression_to_aggregate,
    distinct=False,
    ordering=(),
):
    """
    Get a subquery that aggregates values from a to-many relation as an array.

    Can be used with a many-to-many through model, or any other model with a foreign key to the
    model being annotated.

    Usage examples:

        Interaction.objects.annotate(
            contact_first_names=get_array_agg_subquery(
                Interaction.contacts.through,
                'interaction',
                'first_name',
            ),
        )

        Interaction.objects.annotate(
            adviser_first_names=get_array_agg_subquery(
                InteractionDITParticipant,
                'interaction',
                'first_name',
            ),
        )

    Note: The usage of this function differs from `get_string_agg_subquery()`, as this function
    omits the outer model from the subquery to avoid unwanted NULL values appearing in the
    returned arrays when rows don't have any values in the intermediate model being queried.

    For example, this makes sure an annotation on interaction contacts gets a value of [] if
    the interaction doesn't have any contacts. (If the Interaction model were included in the
    subquery, the annotation value would instead be [None].)
    """
    return get_aggregate_subquery(
        model,
        ArrayAgg(expression_to_aggregate, distinct=distinct, ordering=ordering),
        join_field_name=join_field_name,
    )


def get_aggregate_subquery(model, expression, join_field_name='pk'):
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

    # For an explanation of the operations here, see
    # https://docs.djangoproject.com/en/2.2/ref/models/expressions/#using-aggregates-within-a-subquery-expression
    queryset = model.objects.filter(
        **{join_field_name: OuterRef('pk')},
    ).order_by(
    ).values(
        join_field_name,
    ).annotate(
        _annotated_value=expression,
    ).values(
        '_annotated_value',
    )

    return Subquery(queryset)


def get_top_related_expression_subquery(related_field, expression, ordering, outer_field='pk'):
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
        **{related_field.name: OuterRef(outer_field)},
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
        return get_bracketed_concat_expression(
            'first_name',
            'last_name',
            expression_to_bracket=bracketed_field_name,
        )

    evaluated_bracketed_field_name = (
        f'{person_field_name}__{bracketed_field_name}' if bracketed_field_name else None
    )

    return Case(
        When(
            **{f'{person_field_name}__isnull': False},
            then=get_bracketed_concat_expression(
                f'{person_field_name}__first_name',
                f'{person_field_name}__last_name',
                expression_to_bracket=evaluated_bracketed_field_name,
            ),
        ),
        default=None,
    )


def get_bracketed_concat_expression(*expressions, expression_to_bracket=None):
    """
    Gets an SQL expression that concatenates a number of expressions and optionally another
    field surrounded by brackets.

    For simple annotation of full names of contacts or advisers, get_full_name_expression() should
    be preferred. However, this function can handle other or more complex scenarios.

    Usage examples:

        # Effectively '{Contact.first_name} {Contact.last_name}'
        Contact.objects.annotate(
            name=get_bracketed_concat_expression('first_name', 'last_name'),
        )

        # Effectively '{Contact.first_name} {Contact.last_name} ({Contact.job_title})'
        # (but the job title would be omitted if blank or NULL)
        Contact.objects.annotate(
            name=get_bracketed_concat_expression(
                'first_name',
                'last_name',
                expression_to_bracket='job_title',
            ),
        )

        # Effectively '{Interaction.dit_adviser.first_name} {Interaction.dit_adviser.last_name}'
        Interaction.objects.annotate(
            dit_adviser_name=get_bracketed_concat_expression(
                'dit_adviser__first_name',
                'dit_adviser__last_name',
            ),
        )
    """
    parts = [
        NullIf(field, Value('')) for field in expressions
    ]

    if expression_to_bracket:
        bracketed_expression = PreferNullConcat(
            Value('('),
            NullIf(expression_to_bracket, Value('')),
            Value(')'),
        )
        parts.append(bracketed_expression)

    return ConcatWS(Value(' '), *parts, output_field=CharField())


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


def get_queryset_object(queryset, **filters):
    """
    Safer version of QuerySet.get() that avoids loading all objects into memory when there
    are multiple results.

    (When there are multiple results, QuerySet.get() loads all of them into memory even though
    it raises an exception when multiple matches are found. This can lead to out-of-memory
    situations when there are a very large number of matches. This function avoids that by
    applying a LIMIT to the query.)

    TODO: This will be fixed in Django 3.0 and we should be able to remove this function once
    Django 3.0 has been released and we have updated to it.

    See https://code.djangoproject.com/ticket/6785 for more information.
    """
    return queryset.filter(**filters)[:2].get()


def get_empty_string_if_null_expression(field):
    """Get empty string if field is None."""
    return Coalesce(field, Value(''))
