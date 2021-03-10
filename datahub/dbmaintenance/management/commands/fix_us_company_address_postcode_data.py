from django.db.models import F, Func, Value, Subquery
from django.core.management.base import BaseCommand
from logging import getLogger
import reversion

from datahub.company.models import Company

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to query for the ids of duns-linked companies for a particular set of
    one list tiers and (optionally) particular set of account managers.
    """
    regex = r"'(\d{5}-\d{4})|(\d{5}\s–\s\d{4})" \
            r"|(\d{5}\s-\s\d{4})|(\d{9})|(\d{5})|(\d{1}\s\d{4})'"
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
        self.fix_address_postcodes()
        # self.fix_registered_postcodes()

    @staticmethod
    def fix_registered_postcodes():
        """
        Does update on the postcode address table
        """
        with reversion.create_revision():
            incorrect_registered_postcodes = Command.get_incorrect_formatted_registered_postcodes(
                Command.regex, Command.united_states_id)
            Command.update_registered_address_postcode(incorrect_registered_postcodes)
            logger.info(f'{incorrect_registered_postcodes.count()} records to fix')
            reversion.set_comment('Registered Address Postcode Fix.')

    @staticmethod
    def fix_address_postcodes():
        """
        Does update on the postcode address table
        """
        with reversion.create_revision():
            incorrect_postcodes = Command.get_incorrect_formatted_postcodes(
                Command.regex, Command.united_states_id)
            Command.update_address_postcode(incorrect_postcodes)

            reversion.set_comment('Address Postcode Fix.')

    @staticmethod
    def get_incorrect_formatted_postcodes(regex, united_states_id):
        """
        Get US Company records that have incorrect postcode formats
        """
        result = Company. \
            objects. \
            filter(address_country=united_states_id). \
            exclude(address_postcode__iregex=r'^\d{3}'). \
            annotate(
                fix=Func(
                    Func(
                        Func(
                            F('address_postcode'),
                            Value("' '"),
                            Value("''"),
                            function='replace',
                        ),
                        Value(regex),
                        Value('g'),
                        function='regexp_matches',
                    ),
                    Value("';'"),
                    function='array_to_string',
                ),
            ).values('fix', 'id')
        return result

    @staticmethod
    def get_incorrect_formatted_registered_postcodes(regex, united_states_id):
        """
        Get US Company records that have incorrect registered address postcode formats
        """
        result = Company. \
            objects. \
            filter(registered_address_country=united_states_id). \
            exclude(registered_address_postcode__iregex=r'^\d{3}'). \
            annotate(
                fix=Func(
                    Func(
                        Func(
                            F('registered_address_postcode'),
                            Value("' '"),
                            Value("''"),
                            function='replace',
                        ),
                        Value(regex),
                        Value('g'),
                        function='regexp_matches',
                    ),
                    Value("';'"),
                    function='array_to_string',
                ),
            ).values('id', 'fix')
        return result

    @staticmethod
    def update_address_postcode(subquery):
        """
        Update address postcodes where the subquery exists
        """
        if subquery.count() > 0:
            # Update the postcode
            Company. \
                objects. \
                update(address_postcode=Subquery(subquery.
                                                 values('fix')))
        else:
            logger.info('Nothing to update')

    @staticmethod
    def update_registered_address_postcode(subquery):
        """
        Update registered address postcodes where the subquery exists
        """
        if subquery.count() > 0:
            # Update the postcode
            Company. \
                objects. \
                update(registered_address_postcode=Subquery(subquery))
        else:
            logger.info('Nothing to update')
