import copy

from datahub.bed_api.constants import (
    BusinessArea,
    Classification,
    ContactType,
    DepartmentEyes,
    HighLevelSector,
    InteractionType,
    IssueType,
    JobType,
    LocationsAffected,
    LowLevelSector,
    PolicyArea,
    Salutation,
    SectorsAffected,
    Sentiment,
    TopIssuesByRank,
    TransparencyStatus,
    UkRegionAffected,
)
from datahub.bed_api.utils import remove_blank_from_dict


class BedEntity:
    """Represents a BED  base model"""

    def __init__(self):
        """Constructor for Id based BED entity"""
        self.Id = None

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
        :return: Generated dictionary of all class values as name value pair
        """
        result = copy.deepcopy(self.__dict__)
        return result


class EditAccount(BedEntity):
    """
    Salesforce representation of an Organization/Account edit details
    """

    def __init__(
        self,
        name: str,
        high_level_sector: HighLevelSector,
        low_level_sector: LowLevelSector,
    ):
        """Constructor - Mandatory Fields to be assigned with value *"""
        super().__init__()
        self.Name = name  # *
        self.High_Level_Sector__c = high_level_sector  # *
        self.Low_Level_Sector__c = low_level_sector  # *
        self.Company_Number__c = None
        self.Company_size__c = None  # int value
        self.Companies_House_ID__c = None
        self.BEIS_External_Affairs__c = None
        #  Address
        #  Billing
        self.BillingStreet = None
        self.BillingCity = None
        self.BillingState = None
        self.BillingPostalCode = None
        self.BillingCountry = None
        # Shipping
        self.ShippingStreet = None
        self.ShippingCity = None
        self.ShippingState = None
        self.ShippingPostalCode = None
        self.ShippingCountry = None
        self.UK_Region__c = None
        self.Global_Office_Locations__c = None
        self.Country_HQ__c = None
        self.Location__c = None  # Country
        # Misc
        self.FTSE_100__c = False
        self.FTSE_250__c = False
        self.Multinational__c = False
        self.Company_Website__c = None
        self.EU_Exit_Sentiment__c = None
        self.Parent_Membership_Organisation__c = None
        self.IS_Sentiment__c = None


class EditContact(BedEntity):
    """
    Salesforce representation of a Contact
    """

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
        self.Datahub_ID__c = datahub_id
        self.FirstName = first_name
        self.MiddleName = None
        self.LastName = last_name  # *
        self.Salutation = Salutation.not_applicable
        self.Suffix = None
        self.Email = email  # *
        self.Job_Title__c = None
        self.Job_Type__c: JobType = JobType.none
        self.Notes__c = None
        # Phones
        self.Phone = None
        self.MobilePhone = None
        self.AccountId = account_id  # * Organization Id
        self.Contact_Type__c = ContactType.none
        self.Business_Area__c = BusinessArea.none
        # Assistant details
        self.AssistantName = None
        self.Assistant_Email__c = None
        self.Assistant_Phone__c = None

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
        super().__init__()
        self.Name = name  # *
        self.Datahub_ID__c = datahub_id  # *
        self.Topic__c = title  # *
        self.Date__c = None  # : date
        self.Description__c = None
        self.Interaction_Type__c = InteractionType.none
        self.Webinar_Information__c = None
        # self.Number_of_Attendees__c = None # Readonly
        # Address
        self.Address__c = None
        self.Location__c = None
        self.City_Town__c = None
        self.Region__c = None  # British Region name
        self.Country__c = None  # Country name
        self.Attendees__c = None
        # Misc
        self.For_Your_Eyes_Only__c = False
        self.Contacts_to_share__c = None
        self.Has_Attachment__c = False
        self.iCal_UID__c = None
        self.Show_on_Transparency_Return__c = False
        self.Transparency_Reason_for_meeting__c = None
        self.Transparency_Return_Confirmed__c = False
        self.Transparency_Status__c = TransparencyStatus.none
        self.Issue_Topics__c = None  # list<IssueTopic> delimited with ;
        self.Department_Eyes_Only__c = DepartmentEyes.none
        self.HMG_Lead__c = None  # email
        # Theme
        self.Theme__c = None  # Lookup on Theme ...


class EditEventAttendee(BedEntity):
    """Salesforce representation of an event attendee"""

    def __init__(
        self,
        datahub_id: str,
        event_id: str,
        contact_id: str,
    ):
        """Constructor"""
        super().__init__()
        self.Datahub_ID__c = datahub_id  # *
        self.Event__c = event_id  # *
        self.Attendee__c = contact_id  # *
        self.Name_stub__c = None
        self.Email__c = None


class EditPolicyIssues(BedEntity):
    """Salesforce representation of an interaction or event"""

    def __init__(
        self,
        name: str,
        datahub_id: str,
        issue_type: IssueType,
        account_id: str,
        uk_region_affected: UkRegionAffected,
        policy_area: PolicyArea,
        sectors_affected: SectorsAffected,
        sentiment: Sentiment,
        classification: Classification,

    ):
        """Constructor"""
        super().__init__()
        self.Name = name  # *
        self.Datahub_ID__c = datahub_id  # *
        self.Issue_Type__c = issue_type  # *
        self.Company__c = account_id  # *
        # Company field is a multi-select
        self.UK_Affected__c = uk_region_affected  # *
        self.COVID_19_Related__c = False
        self.Add_Interactions__c = None
        self.For_Your_Eyes_Only__c = False
        self.Policy_Area__c = policy_area  # *
        self.Sectors_Affected__c = sectors_affected  # *
        # Information
        self.Description_of_Issue__c = None
        self.Issue_Closed__c = False
        self.Sentiment__c = sentiment  # *
        self.Classification__c = classification  # *
        self.Show_On_Report__c = False
        self.Top_3_Issue__c = TopIssuesByRank.none
        self.NDP__c = False
        self.Location_s_Affected__c = LocationsAffected.none
        # Impact
        self.Positive_Impact_Value__c = None
        self.Negative_Impact_value__c = None
        self.Number_of_Jobs__c = None
        self.Number_of_Jobs_Lost__c = None
        self.Number_of_Jobs_At_Risk__c = None
        self.Number_of_Jobs_Safeguarded__c = None
