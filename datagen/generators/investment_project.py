from django.db.models.query import QuerySet

from datahub.company.models.adviser import Advisor
from datahub.company.models.company import Company
from datahub.company.models.contact import Contact
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    ContactFactory,
)
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.models import Team


from ..utils import random_object_from_queryset


MODEL_NAME = 'Investment Projects'


def generate_investment_projects(
    number_of_investment_projects: int,
    advisers: list[QuerySet] | None = None,
    companies: list[QuerySet] | None = None,
    contacts: list[QuerySet] | None = None,
):
    if advisers is None:
        number_of_advisers = number_of_investment_projects // 25
        AdviserFactory.create_batch(
            size=number_of_advisers,
            dit_team=random_object_from_queryset(Team.objects.all()),
        )
        print(f'Generated {number_of_advisers} advisers as part of generating {MODEL_NAME.lower()}')  # noqa
        advisers = Advisor.objects.all()

    if companies is None:
        number_of_companies = number_of_investment_projects // 5
        CompanyFactory.create_batch(
            size=number_of_companies,
            created_by=random_object_from_queryset(advisers),
        )
        print(f'Generated {number_of_companies} companies as part of generating {MODEL_NAME.lower()}')  # noqa
        companies = Company.objects.all()

    if contacts is None:
        number_of_contacts = number_of_investment_projects // 10
        ContactFactory.create_batch(
            size=number_of_contacts,
            created_by=random_object_from_queryset(advisers),
            company=random_object_from_queryset(companies),
        )
        print(f'Generated {number_of_contacts} contacts as part of generating {MODEL_NAME.lower()}')  # noqa
        contacts = Contact.objects.all()

    InvestmentProjectFactory.create_batch(
        size=number_of_investment_projects,
        created_by=random_object_from_queryset(advisers),
        investor_company=random_object_from_queryset(companies),
        client_relationship_manager=random_object_from_queryset(advisers),
        referral_source_adviser=random_object_from_queryset(advisers),
        client_contacts=[
            random_object_from_queryset(contacts),
            random_object_from_queryset(contacts),
        ],
    )
