from datahub.bed_api.constants import (
    BusinessArea,
    ContactType,
    HighLevelSector,
    JobType,
    LowLevelSector,
    Salutation,
)
from datahub.bed_api.utils import remove_blank_from_dict


class BedEntity:
    """Represents a BED  base model"""

    data_mapping = dict(id='Id')

    def __init__(self):
        """Constructor for id based BED entity"""
        for key in self.data_mapping.keys():
            setattr(self, key, None)

    def as_values_only_dict(self):
        """
        Generates dictionary with no empty values to optimise data being passed as a dictionary
        Typical scenario is for new records being posted.
        NOTE: If updating be sure to include all values, even blanks,
                as blank may be valid on an update.
        """
        return remove_blank_from_dict(self.as_all_values_dict())

    def as_all_values_dict(self):
        """
        Utilises the internal dictionary to generate all values even if blank

        :return: Generated dictionary of all class values as name value pair
        """
        result = dict()
        for key, sales_force_key in self.data_mapping.items():
            if key in self.__dict__.keys():
                result[sales_force_key] = self.__dict__[key]
            else:
                raise NotImplementedError(f'"{key}" is not found within BED system data mappings')

        return result


class Account(BedEntity):
    """
    Salesforce representation of an Organization/Account edit details
    """

    data_mapping = dict(
        id='Id',
        datahub_id='Datahub_ID__c',
        name='Name',
        high_level_sector='High_Level_Sector__c',
        low_level_sector='Low_Level_Sector__c',
        company_number='Company_Number__c',
        companies_house_id='Companies_House_ID__c',
        billing_street='BillingStreet',
        billing_city='BillingCity',
        billing_state='BillingState',
        billing_postal_code='BillingPostalCode',
        billing_country='BillingCountry',
        shipping_street='ShippingStreet',
        shipping_city='ShippingCity',
        shipping_state='ShippingState',
        shipping_postal_code='ShippingPostalCode',
        shipping_country='ShippingCountry',
        uk_region='UK_Region__c',
        country_hq='Country_HQ__c',
        is_ftse_100='FTSE_100__c',
        is_ftse_250='FTSE_250__c',
        is_multinational='Multinational__c',
        company_website='Company_Website__c',
        eu_exit_sentiment='EU_Exit_Sentiment__c',
        parent_membership_organisation='Parent_Membership_Organisation__c',
        is_sentiment='IS_Sentiment__c',
    )

    def __init__(
        self,
        datahub_id: str,
        name: str,
        high_level_sector: HighLevelSector,
        low_level_sector: LowLevelSector,
    ):
        """Constructor"""
        super().__init__()
        self.name = name
        self.datahub_id = datahub_id
        self.high_level_sector = high_level_sector
        self.low_level_sector = low_level_sector
        self.is_ftse_100 = False
        self.is_ftse_250 = False
        self.is_multinational = False


class Contact(BedEntity):
    """
    Salesforce representation of a Contact
    """

    data_mapping = dict(
        id='Id',
        datahub_id='Datahub_ID__c',
        first_name='FirstName',
        middle_name='MiddleName',
        last_name='LastName',
        salutation='Salutation',
        suffix='Suffix',
        email='Email',
        job_title='Job_Title__c',
        job_type='Job_Type__c',
        notes='Notes__c',
        phone='Phone',
        mobile_phone='MobilePhone',
        account_id='AccountId',
        contact_type='Contact_Type__c',
        business_area='Business_Area__c',
        assistant_name='AssistantName',
        assistant_email='Assistant_Email__c',
        assistant_phone='Assistant_Phone__c',
    )

    def __init__(
        self,
        datahub_id,
        first_name,
        last_name,
        email,
        account_id=None,
    ):
        """Constructor - Mandatory Fields to be assigned with value *"""
        super().__init__()
        self.datahub_id = datahub_id
        self.first_name = first_name
        self.middle_name = None
        self.last_name = last_name
        self.salutation = Salutation.not_applicable
        self.account_id = account_id
        self.suffix = None
        self.email = email
        self.job_title = None
        self.job_type: JobType = JobType.none
        self.notes = None
        self.phone = None
        self.mobile_phone = None
        self.contact_type = ContactType.none
        self.business_area = BusinessArea.none
        self.assistant_name = None
        self.assistant_email = None
        self.assistant_phone = None

    @property
    def name(self):
        """Fullname or name formatted with all name values assigned"""
        names = filter(
            None,
            [
                self.salutation,
                self.first_name,
                self.middle_name,
                self.last_name,
                self.suffix,
            ],
        )
        return ' '.join(names)
