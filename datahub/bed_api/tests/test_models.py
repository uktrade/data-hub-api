
from freezegun import freeze_time

from datahub.bed_api.models import EditContact


class TestEditContactShould:
    """
    Contact expectations
    """

    def test_contact_name_outputs_full_name(self):
        """
        Should format contact name accordingly
        """
        contact = EditContact(
            salutation='Mrs.',
            first_name='Jane',
            last_name='Doe',
            email='jane.doe@email.com',
        )
        contact.MiddleName = 'Middle'
        contact.Suffix = 'Teacher'

        assert contact.name == 'Mrs. Jane Middle Doe Teacher'

    def test_contact_name_outputs_partial_full_name(self):
        """
        Should format contact name accordingly
        """
        contact = EditContact(
            salutation='Mr.',
            first_name=None,
            last_name='Doe',
            email='jane.doe@email.com',
        )

        assert contact.name == 'Mr. Doe'

    @freeze_time('2020-01-01-12:00:00')
    def test_contact_outputs_value_only_generated_dictionary(self):
        """
        Should output contact as dictionary without name, calculated fields
        and empty values
        """
        expected = {
            'Description': 'Test strips unused fields',
            'Email': 'john.doe@email.com',
            'FirstName': 'John',
            'Id': 'Test_Identity',
            'LastName': 'Doe',
            'Salutation': 'Mr.',
        }

        contact = EditContact(
            salutation='Mr.',
            first_name='John',
            last_name='Doe',
            email='john.doe@email.com',
        )
        contact.Description = 'Test strips unused fields'
        contact.Id = 'Test_Identity'

        assert contact.as_blank_clean_dict() == expected
