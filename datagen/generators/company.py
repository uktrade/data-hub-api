from decimal import Decimal

from django.db import transaction
from django.db.models.query import QuerySet

from datahub.company.test.factories import (
    ArchivedCompanyFactory,
    CompanyFactory,
    CompanyWithAreaFactory,
    DuplicateCompanyFactory,
    SubsidiaryFactory,
)

from ..utils import (
    print_progress,
    random_object_from_queryset,
)


COMPANY_TYPE_RATIOS = {
    'company': Decimal('0.5'),
    'company_with_area': Decimal('0.1'),
    'subsidiary_company': Decimal('0.2'),
    'archived_company': Decimal('0.1'),
    'duplicate_company': Decimal('0.1'),
}


def generate_small_number_of_companies(
    number_of_companies: int,
    advisers: list[QuerySet],
):
    comapnies_to_create = []
    for _ in range(number_of_companies):
        adviser = random_object_from_queryset(advisers)
        comapnies_to_create.append(
            CompanyFactory(
                created_by=adviser,
                modified_by=adviser,
            ),
        )
    CompanyFactory._meta.model.objects.bulk_create(comapnies_to_create)
    print(f'Generated {number_of_companies} companies')  # noqa


def generate_companies(
    number_of_companies: int,
    advisers: QuerySet,
):
    print('\nGenerating companies...')  # noqa

    # Handle case when requested number is too small
    if number_of_companies < 10:
        generate_small_number_of_companies(number_of_companies, advisers)
        return

    # Calculate the numbers of each company type to generate
    if sum(COMPANY_TYPE_RATIOS.values()) > 1:
        raise ValueError('Company type ratios must add up to 1')
    target_counts = {
        company_type: round(number_of_companies * ratio)
        for company_type, ratio in COMPANY_TYPE_RATIOS.items()
    }

    # Adjust the counts if rounding affected the totals
    total_target_count = sum(target_counts.values())
    while total_target_count < number_of_companies:
        target_counts['company'] += 1
        total_target_count += 1
    while total_target_count > number_of_companies:
        target_counts['company'] -= 1
        total_target_count -= 1

    # Generate companies
    with transaction.atomic():
        created_so_far = 0
        variants = {
            'company': CompanyFactory,
            'company_with_area': CompanyWithAreaFactory,
            # 'subsidiary_company': SubsidiaryFactory,
            'archived_company': ArchivedCompanyFactory,
            # 'duplicate_company': DuplicateCompanyFactory,
        }
        for variant_name, variant_factory in variants.items():
            # Update progress after adding each type
            print_progress(iteration=created_so_far, total=total_target_count)
            # Create companies, companies with area, and archived companies
            adviser = random_object_from_queryset(advisers)
            instances = variant_factory.create_batch(
                size=target_counts[variant_name],
                created_by=adviser,
                modified_by=adviser,
            )
            created_so_far += target_counts[variant_name]
            if variant_name == 'company':
                companies_list = instances

        # Create subsidiaries
        adviser = random_object_from_queryset(advisers)
        SubsidiaryFactory.create_batch(
            size=target_counts['subsidiary_company'],
            created_by=adviser,
            modified_by=adviser,
            global_headquarters=companies_list[0],
        )
        created_so_far += target_counts['subsidiary_company']
        print_progress(iteration=created_so_far, total=total_target_count)

        # Create duplicate companies
        adviser = random_object_from_queryset(advisers)
        DuplicateCompanyFactory.create_batch(
            size=target_counts['duplicate_company'],
            created_by=adviser,
            modified_by=adviser,
            transferred_by=adviser,
            transferred_to=companies_list[1],
        )
        created_so_far += target_counts['duplicate_company']
        print_progress(iteration=created_so_far, total=total_target_count)

        print(f'\nGenerated {total_target_count} companies')  # noqa
