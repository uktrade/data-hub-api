from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_decimal, parse_uuid
from datahub.interaction.models import Interaction


class Command(CSVBaseCommand):
    """Command to update grant-related fields for service deliveries."""

    def add_arguments(self, parser):
        """Define extra arguments."""
        super().add_arguments(parser)
        parser.add_argument(
            '--overwrite',
            action='store_true',
            default=False,
            help='If passed, existing non-null values will be overwritten.',
        )

    def _process_row(self, row, simulate=False, overwrite=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        status_id = parse_uuid(row['status_id'])
        grant_amount_offered = parse_decimal(row['grant_offered'])
        net_company_receipt = parse_decimal(row['net_company_receipt'])

        interaction = Interaction.objects.get(pk=pk)

        something_updated = _update_fields(
            interaction, status_id, grant_amount_offered, net_company_receipt, overwrite,
        )

        if simulate or not something_updated:
            return

        interaction.save(
            update_fields=(
                'service_delivery_status',
                'grant_amount_offered',
                'net_company_receipt',
            ),
        )


def _update_fields(interaction, status_id, grant_amount_offered, net_company_receipt, overwrite):
    if interaction.kind != Interaction.KINDS.service_delivery:
        raise ValueError('Cannot set grant fields on interactions without kind==service_delivery')

    status_updated = _update_field(
        interaction, 'service_delivery_status_id', status_id, overwrite,
    )
    grant_amount_offered_updated = _update_field(
        interaction, 'grant_amount_offered', grant_amount_offered, overwrite,
    )
    net_company_receipt_updated = _update_field(
        interaction, 'net_company_receipt', net_company_receipt, overwrite,
    )

    return status_updated or grant_amount_offered_updated or net_company_receipt_updated


def _update_field(interaction, field, new_value, overwrite):
    old_value = getattr(interaction, field)
    should_update = (overwrite or not old_value) and old_value != new_value

    if should_update:
        setattr(interaction, field, new_value)

    return should_update
