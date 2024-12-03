from django.db import transaction
from django.db.models.query import QuerySet

from datahub.company.test.factories import ContactFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory

from ..utils import (
    print_progress,
    random_object_from_queryset,
)


def generate_investment_projects(
    number_of_investment_projects: int,
    advisers: QuerySet,
    companies: QuerySet,
):
    print('\nGenerating investment projects...')  # noqa
    with transaction.atomic():
        # Pre-create contacts for all companies and store in dict
        companies = companies[:number_of_investment_projects]
        contacts_by_company = {
            company: ContactFactory(
                created_by=random_object_from_queryset(advisers),
                company=company,
            )
            for company in companies
        }

        # Calculate number of projects per company and the remainder
        projects_per_company, remainder = divmod(number_of_investment_projects, companies.count())

        created_so_far = 0
        for index, company in enumerate(companies):
            # Update progress every 20 iterations and on the last iteration
            if (index + 1) % 20 == 0 or index == number_of_investment_projects - 1:
                print_progress(iteration=created_so_far, total=number_of_investment_projects)

            # Handle remainder
            projects_to_create_for_company = projects_per_company
            if remainder:
                projects_to_create_for_company += 1
                remainder -= 1

            adviser = random_object_from_queryset(advisers)
            contact = contacts_by_company[company]

            # Create batch of projects for each company and an adviser
            InvestmentProjectFactory.create_batch(
                size=projects_to_create_for_company,
                created_by=adviser,
                investor_company=company,
                client_relationship_manager=adviser,
                referral_source_adviser=adviser,
                client_contacts=[contact],
            )
            created_so_far += projects_to_create_for_company

        print(f'\nGenerated {number_of_investment_projects} investment projects')  # noqa
        print(f'Also generated {len(companies)} company contacts') # noqa
