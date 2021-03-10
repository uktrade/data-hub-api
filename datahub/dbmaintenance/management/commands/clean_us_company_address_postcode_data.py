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

    def add_arguments(self, parser):
        """
        No arguments needed for the management command.
        """
        pass

    def handle(self, *args, **options):
        """
        Run the query and output the results as an info message to the log file.
        """
        self.clean_address_postcode()

    @staticmethod
    def clean_address_postcode():
        """
        Does update on the postcode address table
        """
        with reversion.create_revision():
            regex = r"'(\d{5}-\d{4})|(\d{5}\s–\s\d{4})" \
                    r"|(\d{5}\s-\s\d{4})|(\d{9})|(\d{5})|(\d{1}\s\d{4})'"
            united_states_id = '81756b9a-5d95-e211-a939-e4115bead28a'
            sub = Command.get_error_postcodes(regex, united_states_id)
            Command.update_address_postcode(sub)

            reversion.set_comment('Address Postcode Fix.')

    @staticmethod
    def get_error_postcodes(regex, united_states_id):
        sub = Company. \
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
            ).values('fix')
        return sub

    @staticmethod
    def update_address_postcode(sub):
        if sub.count() > 0:
            # Update the postcode
            Company. \
                objects. \
                update(address_postcode=Subquery(sub))
        else:
            logger.info('Nothing to update')
