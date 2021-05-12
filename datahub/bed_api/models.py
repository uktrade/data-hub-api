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
        self.Name = name  # *
        self.High_Level_Sector__c = high_level_sector  # *
        self.Low_Level_Sector__c = low_level_sector  # *
        self.Company_Number__c = None
        self.Company_size__c = None
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
        self.Location__c = None
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
        salutation,
        first_name,
        last_name,
        email,
        account_id=None,
    ):
        """Constructor - Mandatory Fields to be assigned with value *"""
        super().__init__()
        self.FirstName = first_name
        self.MiddleName = None
        self.LastName = last_name  # *
        self.Salutation = salutation
        self.Suffix = None
        self.Email = email  # *
        self.Job_Title__c = None
        self.Job_Type__c = None
        self.Notes__c = None
        # Phones
        self.Phone = None
        self.MobilePhone = None
        self.AccountId = account_id  # * Organization Id
        self.Contact_Type__c = None
        # Business Sector e.g. 'Advanced Manufacturing;Professional & Business Services'
        self.Business_Area__c = None

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
