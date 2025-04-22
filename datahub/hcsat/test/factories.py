import factory
from factory.fuzzy import FuzzyText

from datahub.hcsat.models import CustomerSatisfactionToolFeedback


class CustomerSatisfactionToolFeedbackFactory(factory.django.DjangoModelFactory):
    """Factory for CustomerSatisfactionToolFeedback."""

    url = factory.Faker('url')
    was_useful = factory.Faker('pybool')

    did_not_find_what_i_wanted = factory.Maybe(
        'was_useful',
        yes_declaration=False,
        no_declaration=factory.Faker('pybool'),
    )
    difficult_navigation = factory.Maybe(
        'was_useful',
        yes_declaration=False,
        no_declaration=factory.Faker('pybool'),
    )
    lacks_feature = factory.Maybe(
        'was_useful',
        yes_declaration=False,
        no_declaration=factory.Faker('pybool'),
    )
    unable_to_load = factory.Maybe(
        'was_useful',
        yes_declaration=False,
        no_declaration=factory.Faker('pybool'),
    )
    inaccurate_information = factory.Maybe(
        'was_useful',
        yes_declaration=False,
        no_declaration=factory.Faker('pybool'),
    )
    other_issues = factory.Maybe(
        'was_useful',
        yes_declaration=False,
        no_declaration=factory.Faker('pybool'),
    )
    other_issues_detail = factory.Maybe(
        'other_issues',
        yes_declaration=FuzzyText(),
        no_declaration='',
    )
    improvement_suggestion = factory.Maybe(
        'was_useful',
        yes_declaration='',
        no_declaration=FuzzyText(),
    )

    class Meta:
        model = CustomerSatisfactionToolFeedback
