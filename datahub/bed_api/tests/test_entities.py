from datahub.bed_api.constants import HighLevelSector, LowLevelSector, Salutation
from datahub.bed_api.entities import Account, Contact


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


class TestEditContactShould:
    """
    Contact expectations
    """

    def test_contact_name_outputs_full_name(self):
        """
        Should format contact name accordingly
        """
        contact = Contact(
            datahub_id='datahub_id',
            first_name='Jane',
            last_name='Doe',
            email='jane.doe@email.com',
        )
        contact.salutation = Salutation.mrs
        contact.middle_name = 'Middle'
        contact.suffix = 'Teacher'

        assert contact.name == 'Mrs. Jane Middle Doe Teacher'

    def test_contact_name_outputs_partial_full_name(self):
        """
        Should format contact name accordingly
        """
        contact = Contact(
            datahub_id='datahub_id',
            first_name=None,
            last_name='Doe',
            email='jane.doe@email.com',
        )
        contact.salutation = Salutation.mr

        assert contact.name == 'Mr. Doe'

    def test_contact_outputs_value_only_generated_dictionary(self):
        """
        Should output contact as dictionary without name, calculated fields
        and empty values
        """
        expected = {
            'Datahub_ID__c': 'datahub_id',
            'Email': 'john.doe@email.com',
            'FirstName': 'John',
            'Id': 'Test_Identity',
            'LastName': 'Doe',
            'Salutation': 'Mr.',
        }

        contact = Contact(
            datahub_id='datahub_id',
            first_name='John',
            last_name='Doe',
            email='john.doe@email.com',
        )
        contact.salutation = Salutation.mr
        contact.id = 'Test_Identity'
        assert contact.as_values_only_dict() == expected
