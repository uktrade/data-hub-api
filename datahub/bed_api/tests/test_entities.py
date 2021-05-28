from datahub.bed_api.constants import HighLevelSector, LowLevelSector
from datahub.bed_api.entities import Account


class TestEditAccountShould:
    """
    Contact expectations
    """

    def test_account_outputs_value_only_generated_dictionary(self):
        """
        Should output account as dictionary without name, calculated fields
        and empty values and should map to the BED account names
        """
        expected = {
            'Datahub_ID__c': 'datahub_id',
            'FTSE_100__c': False,
            'FTSE_250__c': False,
            'High_Level_Sector__c': 'Energy',
            'Id': 'Test_Identity',
            'Low_Level_Sector__c': 'Telecoms',
            'Multinational__c': False,
            'Name': 'Company Name',
        }

        account = Account(
            datahub_id='datahub_id',
            name='Company Name',
            high_level_sector=HighLevelSector.energy,
            low_level_sector=LowLevelSector.telecoms,
        )
        account.id = 'Test_Identity'
        assert account.as_values_only_dict() == expected
