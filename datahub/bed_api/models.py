from datetime import datetime

from datahub.bed_api.utils import remove_blank_from_dict


class BedEntity:
    """Represents a BED  base model"""

    def __init__(self):
        """Constructor for Id based BED entity"""
        self.Id = None
        self.ParentId = None
        self.IsDeleted = False
        self.Description = None
        self.Name = None
        self.LastModifiedDate = datetime.now()
        self.LastModifiedById = None
        self.CreatedById = None
        self.CreatedDate = datetime.now()
        self.SystemModstamp = datetime.now()

    def as_blank_clean_dict(self):
        """
        Generates dictionary with no empty values to optimise data being passed as a dictionary
        Typical scenario is for new records being posted.
        NOTE: If updating be sure to include all values, even blanks,
                as blank may be valid on an update.
        """
        result = remove_blank_from_dict(self.__dict__)
        return result


class Account(BedEntity):
    """
    Salesforce representation of an Organization
    """

    def __init__(
            self,
            name,
    ):
        """Constructor - Mandatory Fields to be assigned with value *"""
        super().__init__()
        self.Name = name  # *
        self.High_Level_Sector__c = None  # *
        # Digital;Infrastructure;Telecoms
        self.Low_Level_Sector__c = None  # *
        self.Company_Number__c = None
        self.Company_size__c = None
        self.Companies_House_ID__c = None
        self.BEIS_External_Affairs__c = None
        #  Address
        self.BillingAddress: Address = None
        self.ShippingAddress: Address = None
        self.UK_Region__c = None   # *
        self.Global_Office_Locations__c = None   # *
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


class Contact(BedEntity):
    """
    Salesforce representation of a Contact
    """

    def __init__(
            self,
            salutation,
            first_name,
            last_name,
            email,
            record_type_id=None,
            account_id=None,
            owner_id=None,
            last_modified_by_id=None,
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
        # Address
        self.MailingStreet = None
        self.MailingCity = None
        self.MailingState = None
        self.MailingPostalCode = None
        self.MailingCountry = None
        self.MailingAddress: Address = None
        self.OtherAddress: Address = None
        # Phones
        self.Phone = None
        self.MobilePhone = None
        # Misc lookup fields
        self.RecordTypeId = record_type_id  # Contact Record Type
        self.AccountId = account_id  # * Organization Id
        self.OwnerId = owner_id
        self.Contact_Type__c = None
        self.LastModifiedById = last_modified_by_id
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


class Address:
    """Bed Address"""

    def __init__(self):
        """Constructor"""
        self.Street = None
        self.City = None
        self.PostalCode = None
        self.State = None
        self.Country = None
        # Mailing, Shipping, Billing, Home
        self.AddressType = None
