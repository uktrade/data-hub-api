from datetime import date

from datahub.bed_api.constants import (
    BusinessArea,
    ContactType,
    DepartmentEyes,
    HighLevelSector,
    InteractionType,
    JobType,
    LowLevelSector,
    Salutation,
    TransparencyStatus,
)
from datahub.bed_api.utils import remove_blank_from_dict


class BedEntity:
    """Represents a BED  base model"""

    def __init__(self):
        """Constructor for Id based BED entity"""
        self.Id: str = None

    def as_values_only_dict(self):
        """
        Generates dictionary with no empty values to optimise data being passed as a dictionary
        Typical scenario is for new records being posted.
        NOTE: If updating be sure to include all values, even blanks,
                as blank may be valid on an update.
        """
        result = remove_blank_from_dict(self.as_all_values_dict())
        return result

    def as_all_values_dict(self):
        """
        Utilises the internal dictionary to generate all values even if blank
        @return: Generated dictionary of all class values as name value pair
        """
        return self.__dict__


class EditAccount(BedEntity):
    """
    Salesforce representation of an Organization/Account edit details
    """

    def __init__(
            self,
            name,
            high_level_sector,
            low_level_sector,
    ):
        """Constructor - Mandatory Fields to be assigned with value *"""
        super().__init__()
        self.Name: str = name  # *
        self.High_Level_Sector__c: HighLevelSector = high_level_sector  # *
        self.Low_Level_Sector__c: LowLevelSector = low_level_sector  # *
        self.Company_Number__c: str = None
        self.Company_size__c: int = None
        self.Companies_House_ID__c: str = None
        self.BEIS_External_Affairs__c: str = None
        #  Address
        #  Billing
        self.BillingStreet: str = None
        self.BillingCity: str = None
        self.BillingState: str = None
        self.BillingPostalCode: str = None
        self.BillingCountry: str = None
        # Shipping
        self.ShippingStreet: str = None
        self.ShippingCity: str = None
        self.ShippingState: str = None
        self.ShippingPostalCode: str = None
        self.ShippingCountry: str = None
        self.UK_Region__c: str = None
        self.Global_Office_Locations__c: str = None
        self.Country_HQ__c: str = None
        self.Location__c: str = None  # Country
        # Misc
        self.FTSE_100__c: bool = False
        self.FTSE_250__c: bool = False
        self.Multinational__c: bool = False
        self.Company_Website__c: str = None
        self.EU_Exit_Sentiment__c: str = None
        self.Parent_Membership_Organisation__c: str = None
        self.IS_Sentiment__c = None


class EditContact(BedEntity):
    """
    Salesforce representation of a Contact
    """

    def __init__(
            self,
            first_name,
            last_name,
            email,
            account_id=None,
    ):
        """Constructor - Mandatory Fields to be assigned with value *"""
        super().__init__()
        self.FirstName: str = first_name
        self.MiddleName: str = None
        self.LastName: str = last_name  # *
        self.Salutation: Salutation = Salutation.not_applicable
        self.Suffix: str = None
        self.Email: str = email  # *
        self.Job_Title__c: str = None
        self.Job_Type__c: JobType = None
        self.Notes__c: str = None
        # Phones
        self.Phone: str = None
        self.MobilePhone: str = None
        self.AccountId: str = account_id  # * Organization Id
        self.Contact_Type__c: ContactType = None
        self.Business_Area__c: BusinessArea = None
        # Assistant details
        self.AssistantName: str = None
        self.Assistant_Email__c: str = None
        self.Assistant_Phone__c: str = None

    @property
    def name(self):
        """Fullname or name formatted with all name values assigned"""
        names = filter(
            None,
            [
                self.Salutation,
                self.FirstName,
                self.MiddleName,
                self.LastName,
                self.Suffix,
            ],
        )
        return ' '.join(names)


class EditEvent(BedEntity):
    """Salesforce representation of an interaction or event"""

    def __init__(
        self,
        name: str,
        datahub_id: str,
        title: str = None,
    ):
        """Constructor"""
        self.Name: str = name  # *
        self.Datahub_ID__c: str = datahub_id  # *
        self.Topic__c: str = title  # *
        self.Date__c: date = None
        self.Description__c: str = None
        self.Interaction_Type__c: InteractionType = None
        self.Webinar_Information__c: str = None
        # self.Number_of_Attendees__c: int = None # Readonly
        # Address
        self.Address__c: str = None
        self.Location__c: str = None
        self.City_Town__c: str = None
        self.Region__c: str = None  # British Region name
        self.Country__c: str = None  # Country name
        self.Attendees__c: str = None
        # Misc
        self.For_Your_Eyes_Only__c: bool = False
        self.Contacts_to_share__c: str = None
        self.Has_Attachment__c: bool = False
        self.iCal_UID__c: str = None
        self.Show_on_Transparency_Return__c: bool = False
        self.Transparency_Reason_for_meeting__c: str = None
        self.Transparency_Return_Confirmed__c: bool = False
        self.Transparency_Status__c: TransparencyStatus = None
        self.Issue_Topics__c: str = None  # list<IssueTopic> delimited with ;
        self.Department_Eyes_Only__c: DepartmentEyes = None
        self.HMG_Lead__c: str = None  # email
        # Theme
        self.Theme__c: str = None  # Lookup on Theme ...
