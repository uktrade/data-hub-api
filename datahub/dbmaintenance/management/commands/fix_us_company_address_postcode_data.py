from django.db.models import F, Func, Value
from django.core.management.base import BaseCommand
from logging import getLogger
import reversion

from datahub.company.models import Company

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to query for the ids of duns-linked companies for a particular set of
    one list tiers and (optionally) particular set of account managers.
    Note - Online Tests and interactions can be found here at https://regex101.com/r/yckIVj/2
    """
    regex = r'^.*?(?:(\d{5}-\d{4})|(\d{5}\s-\s\d{4})|(\d{5}\s–\s\d{4})|(\d{9})|(\d\s?\d{4})).*?$'
    united_states_id = '81756b9a-5d95-e211-a939-e4115bead28a'

    def add_arguments(self, parser):
        """
        No arguments needed for the management command.
        """
        pass

    def handle(self, *args, **options):
        """
        Run the query and output the results as an info message to the log file.
        """
        Command.fix_postcodes()

    @staticmethod
    def fix_postcodes():
        """
        Does update on the postcode address table
        """
        with reversion.create_revision():
            Command.update_address_postcode()
            Command.update_registered_address_postcode()
            reversion.set_comment('Address Postcode Fix.')

    @staticmethod
    def update_address_postcode():
        """
        Update address postcodes where the subquery exists
        """
        Company \
            .objects \
            .filter(address_country=Command.united_states_id) \
            .update(
                address_postcode=Func(
                    F('address_postcode'),
                    Value(Command.regex),
                    Value(r'\1\2\3\4'),
                    Value('gm'),
                    function='regexp_replace'))

    @staticmethod
    def update_registered_address_postcode():
        """
        Update registered address postcodes where the subquery exists
        """

        Company \
            .objects \
            .filter(address_country=Command.united_states_id) \
            .update(
                registered_address_postcode=Func(
                    F('registered_address_postcode'),
                    Value(Command.regex),
                    Value(r'\1\2\3\4'),
                    Value('gm'),
                    function='regexp_replace'))
