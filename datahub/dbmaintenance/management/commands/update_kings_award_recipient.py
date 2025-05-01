from logging import getLogger

import reversion
from django.core.exceptions import ValidationError

from datahub.company.models import Company
from datahub.company_activity.models import KingsAwardRecipient
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_int, parse_limited_string

logger = getLogger(__name__)

CSV_CATEGORY_TO_MODEL_CATEGORY = {
    'International Trade': KingsAwardRecipient.Category.INTERNATIONAL_TRADE,
    'Innovation': KingsAwardRecipient.Category.INNOVATION,
    'Export and Technology': KingsAwardRecipient.Category.EXPORT_AND_TECHNOLOGY,
    'Sustainable Development': KingsAwardRecipient.Category.SUSTAINABLE_DEVELOPMENT,
    'Promoting Opportunity': KingsAwardRecipient.Category.PROMOTING_OPPORTUNITY,
}


class Command(CSVBaseCommand):
    help = """
    Ingest King's Award data from a CSV stored in S3.

    Columns expected:
    - company_number
    - year_awarded
    - category_name
    - citation
    - year_expired
    """

    def _process_row(self, row, simulate=False, **options):
        company_number = parse_limited_string(row['company_number'].strip())
        year_awarded = parse_int(row['year_awarded'])
        category_name = parse_limited_string(row['category_name'].strip())
        citation = parse_limited_string(row['citation'])
        year_expired = parse_int(row['year_expired'])

        try:
            company = Company.objects.get(company_number=company_number)
        except Company.DoesNotExist:
            logger.warning(
                f'Skipping - Company with Companies House number {company_number} does not exist.',
            )
            return

        category_enum_value = CSV_CATEGORY_TO_MODEL_CATEGORY.get(category_name)
        if not category_enum_value:
            logger.warning(
                f"Skipping - Invalid category name '{category_name}' for {company_number} [{company.id}, {company.name}].",
            )
            return

        award = KingsAwardRecipient(
            company=company,
            year_awarded=year_awarded,
            category=category_enum_value,
            citation=citation,
            year_expired=year_expired,
        )

        try:
            award.clean_fields()  # static validation (django min value validator)
            award.clean()  # dynamic validation (custom max value validator)
        except ValidationError as e:
            error_message = ', '.join(
                [f'{field}: {"; ".join(msgs)}' for field, msgs in e.message_dict.items()],
            )
            logger.warning(
                f'Skipping - Validation failed for {company_number} [{company.id}, {company.name}] - {error_message}',
            )
            return

        if simulate:
            logger.info(
                f"Simulate create/update King's Award for {company_number} [{company.id}, {company.name}] - {year_awarded} {category_enum_value}.",
            )
            return

        try:
            with reversion.create_revision():
                award, created = KingsAwardRecipient.objects.update_or_create(
                    company=company,
                    category=category_enum_value,
                    year_awarded=year_awarded,
                    defaults={
                        'citation': citation,
                        'year_expired': year_expired,
                    },
                )

                action = 'Created' if created else 'Updated'
                reversion.set_comment(f"{action} King's Award recipient via ingest command.")
                logger.info(
                    f"{action} King's Award recipient {award.id} for {company.name} - {year_awarded} {category_enum_value}.",
                )
        except Exception as e:
            logger.error(
                f"Error processing King's Award recipient for {company_number} [{company.id}, {company.name}] - {e}",
            )
            raise  # re-raise to ensure the row is propagated as failed to the base command
