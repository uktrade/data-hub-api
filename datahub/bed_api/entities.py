from datahub.bed_api.constants import (
    BusinessArea,
    Classification,
    ContactType,
    DepartmentEyes,
    HighLevelSector,
    InteractionType,
    IssueType,
    JobType,
    LowLevelSector,
    RegionOrInternational,
    Salutation,
    Sentiment,
    TopIssuesByRank,
    TransparencyStatus,
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
        """Constructor"""
        super().__init__()
        self.datahub_id = datahub_id
        self.first_name = first_name
        self.last_name = last_name
        self.salutation = Salutation.not_applicable
        self.account_id = account_id
        self.email = email
        self.job_type: JobType = JobType.none
        self.contact_type = ContactType.none
        self.business_area = BusinessArea.none

    @property
    def name(self):
        """Fullname or name formatted with all name values assigned"""
        names = filter(
            bool,
            [
                self.salutation,
                self.first_name,
                self.middle_name,
                self.last_name,
                self.suffix,
            ],
        )
        return ' '.join(names)


class Event(BedEntity):
    """Salesforce representation of an interaction or event"""

    data_mapping = dict(
        id='Id',
        name='Name',
        datahub_id='Datahub_ID__c',
        title='Topic__c',
        event_date='Date__c',
        description='Description__c',
        interaction_type='Interaction_Type__c',
        webinar_information='Webinar_Information__c',
        address='Address__c',
        location='Location__c',
        city_town='City_Town__c',
        region='Region__c',
        country='Country__c',
        attendees='Attendees__c',
        is_for_your_eyes_only='For_Your_Eyes_Only__c',
        contacts_to_share='Contacts_to_share__c',
        has_attachment='Has_Attachment__c',
        is_show_on_transparency_return='Show_on_Transparency_Return__c',
        transparency_reason_for_meeting='Transparency_Reason_for_meeting__c',
        is_transparency_return_confirmed='Transparency_Return_Confirmed__c',
        transparency_status='Transparency_Status__c',
        issue_topics='Issue_Topics__c',
        department_eyes_only='Department_Eyes_Only__c',
        hmg_lead_email='HMG_Lead__c',
        theme_id='Theme__c',
    )

    def __init__(
        self,
        name: str,
        datahub_id: str,
        title: str = None,
    ):
        """Constructor"""
        super().__init__()
        self.name = name
        self.datahub_id = datahub_id
        self.title = title
        self.interaction_type = InteractionType.none
        self.region = RegionOrInternational.none
        self.is_for_your_eyes_only = False
        self.has_attachment = False
        self.is_show_on_transparency_return = False
        self.is_transparency_return_confirmed = False
        self.transparency_status = TransparencyStatus.none
        self.department_eyes_only = DepartmentEyes.none


class EventAttendee(BedEntity):
    """Salesforce representation of an event attendee"""

    data_mapping = dict(
        id='Id',
        datahub_id='Datahub_ID__c',
        event_id='Event__c',
        attendee_id='Attendee__c',
        name='Name_stub__c',
        email='Email__c',
    )

    def __init__(
        self,
        datahub_id: str,
        event_id: str,
        contact_id: str,
    ):
        """Constructor"""
        super().__init__()
        self.datahub_id = datahub_id
        self.event_id = event_id
        self.attendee_id = contact_id


class PolicyIssues(BedEntity):
    """Salesforce representation of an interaction or event"""

    data_mapping = dict(
        id='Id',
        datahub_id='Datahub_ID__c',
        name='Name',
        issue_type='Issue_Type__c',
        account_id='Company__c',
        policy_areas='Policy_Area__c',
        sectors_affected='Sectors_Affected__c',
        sentiment='Sentiment__c',
        classification='Classification__c',
        uk_region_affected='UK_Affected__c',
        is_covid_19_related='COVID_19_Related__c',
        event_id='Add_Interactions__c',
        is_for_your_eyes_only='For_Your_Eyes_Only__c',
        description='Description_of_Issue__c',
        is_issue_closed='Issue_Closed__c',
        can_show_on_report='Show_On_Report__c',
        issue_rank='Top_3_Issue__c',
        is_ndp='NDP__c',
        location_affected='Location_s_Affected__c',
        positive_impact_value='Positive_Impact_Value__c',
        negative_impact_value='Negative_Impact_value__c',
        number_of_jobs='Number_of_Jobs__c',
        number_of_jobs_lost='Number_of_Jobs_Lost__c',
        number_of_jobs_at_risk='Number_of_Jobs_At_Risk__c',
        number_of_jobs_safeguarded='Number_of_Jobs_Safeguarded__c',
    )

    def __init__(
        self,
        name: str,
        datahub_id: str,
        event_id: str,
        issue_type: IssueType,
        account_id: str,
        uk_region_affected: RegionOrInternational.none,
        policy_areas: str,  # Delimited list of PolicyArea
        sectors_affected: str,  # Delimited list of SectorsAffected
        sentiment: Sentiment = Sentiment.none,
        classification: Classification = Classification.none,
    ):
        """Constructor"""
        super().__init__()
        self.name = name
        self.datahub_id = datahub_id
        self.issue_type = issue_type
        self.account_id = account_id
        self.policy_areas = policy_areas
        self.sectors_affected = sectors_affected
        self.sentiment = sentiment
        self.classification = classification
        self.uk_region_affected = uk_region_affected
        self.is_covid_19_related = False
        self.event_id = event_id
        self.is_for_your_eyes_only = False
        self.is_issue_closed = False
        self.can_show_on_report = False
        self.issue_rank = TopIssuesByRank.none
        self.is_ndp = False
        self.location_affected = RegionOrInternational.none
