import os

from simple_salesforce import Salesforce


class BedFactory:
    """
    Bed factory for creating Salesforce instance
    """

    def create(self):
        """
        Create a Salesforce instance with configured settings

        :return: Salesforce instance
        """
        if os.environ.get('BED_IS_SANDBOX', '').lower() == 'true':
            return Salesforce(
                username=os.environ['BED_USERNAME'],
                password=os.environ['BED_PASSWORD'],
                security_token=os.environ['BED_TOKEN'],
                domain='test',
            )
        return Salesforce(
            username=os.environ['BED_USERNAME'],
            password=os.environ['BED_PASSWORD'],
            security_token=os.environ['BED_TOKEN'],
        )
