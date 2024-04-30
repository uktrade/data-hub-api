from django.db.models.query import QuerySet

from datahub.company.test.factories import ContactFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory

from ..utils import (
    random_object_from_queryset,
    send_heartbeat_every_10_iterations,
)


def generate_investment_projects(
    number_of_investment_projects: int,
    advisers: list[QuerySet],
    companies: list[QuerySet],
):
    projects_per_company = number_of_investment_projects // companies.count()
    for index, company in enumerate(companies):
        adviser = random_object_from_queryset(advisers)
        contact = ContactFactory(
            created_by=adviser,
            company=company,
        )
        InvestmentProjectFactory.create_batch(
            size=projects_per_company,
            created_by=adviser,
            investor_company=company,
            client_relationship_manager=adviser,
            referral_source_adviser=adviser,
            client_contacts=[
                contact,
            ],
        )
        send_heartbeat_every_10_iterations(index)
    print(f'\nGenerated {number_of_investment_projects} investment projects')  # noqa
    print(f'Also generated {len(companies)} contacts') # noqa
