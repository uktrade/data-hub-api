import itertools
import datahub.company.models as company
import datahub.interaction.models as interaction
import datahub.metadata.models as metadata
from datahub.korben.etl.mapping import Mapping, MetadataMapping

metadata_specs = (
    (
        'optevia_businesstypeId',
        'optevia_businesstypeSet',
        'optevia_name',
        metadata.BusinessType
    ),
    (
        'optevia_sectorId',
        'optevia_sectorSet',
        'optevia_name',
        metadata.Sector
    ),
    (
        'optevia_employeerangeId',
        'optevia_employeerangeSet',
        'optevia_name',
        metadata.EmployeeRange
    ),
    (
        'optevia_turnoverrangeId',
        'optevia_turnoverrangeSet',
        'optevia_name',
        metadata.TurnoverRange
    ),
    (
        'optevia_ukregionId',
        'optevia_ukregionSet',
        'optevia_name',
        metadata.UKRegion
    ),
    (
        'optevia_countryId',
        'optevia_countrySet',
        'optevia_Country',
        metadata.Country
    ),
    (
        'optevia_titleId',
        'optevia_titleSet',
        'optevia_name',
        metadata.Title
    ),
    (
        'optevia_contactroleId',
        'optevia_contactroleSet',
        'optevia_name',
        metadata.Role
    ),
    (
        'optevia_interactioncommunicationchannelId',
        'optevia_interactioncommunicationchannelSet',
        'optevia_name',
        metadata.InteractionType
    ),
    (
        'BusinessUnitId',
        'BusinessUnitSet',
        'Name',
        metadata.Team
    ),
    (
        'optevia_serviceId',
        'optevia_serviceSet',
        'optevia_name',
        metadata.Service
    ),
    (
        'optevia_servicedeliverystatusId',
        'optevia_servicedeliverystatusSet',
        'optevia_name',
        metadata.ServiceDeliveryStatus
    ),
)

mappings = tuple(itertools.starmap(MetadataMapping, metadata_specs)) + (
    Mapping(from_entitytype='AccountSet', ToModel=company.Company, fields=(
            ('AccountId', 'id'),
            ('Name', 'name'),
            ('optevia_Alias', 'alias'),
            ('optevia_CompaniesHouseNumber', 'company_number'),
            ('optevia_Address1', 'registered_address_1'),
            ('optevia_Address2', 'registered_address_2'),
            ('optevia_Address3', 'registered_address_3'),
            ('optevia_Address4', 'registered_address_4'),
            ('optevia_TownCity', 'registered_address_town'),
            ('optevia_StateCounty', 'registered_address_county'),
            ('optevia_PostCode', 'registered_address_postcode'),
            ('Description', 'description'),
            ('WebSiteURL', 'website'),
            ('ModifiedOn', 'modified_on'),
            ('CreatedOn', 'created_on'),
            ('optevia_Country.Id', 'registered_address_country_id'),
            ('optevia_UKRegion.Id', 'uk_region_id'),
            ('optevia_BusinessType.Id', 'business_type_id'),
            ('optevia_Sector.Id', 'sector_id'),
            ('optevia_EmployeeRange.Id', 'employee_range_id'),
            ('optevia_TurnoverRange.Id', 'turnover_range_id'),
        ),
        undef=(
            'registered_address_country_id',
            'business_type_id',
            'sector_id',
            'uk_region_id',
        ),
    ),
    Mapping(
        from_entitytype='SystemUserSet', ToModel=company.Advisor, fields=(
            ('SystemUserId', 'id'),
            ('FirstName', 'first_name'),
            ('LastName', 'last_name'),
            ('DomainName', 'email'),
            ('BusinessUnitId.Id', 'dit_team_id'),
        ),
        concat=((('FirstName', 'MiddleName'), 'first_name'),),
    ),
    Mapping(from_entitytype='ContactSet', ToModel='company_contact', fields=(
            ('ContactId', 'id'),
            ('JobTitle', 'job_title'),
            ('LastName', 'last_name'),
            ('optevia_PrimaryContact', 'primary'),
            ('optevia_CountryCode', 'telephone_countrycode'),
            ('EMailAddress1', 'email'),
            ('optevia_Address1', 'address_1'),
            ('optevia_Address2', 'address_2'),
            ('optevia_Address3', 'address_3'),
            ('optevia_Address4', 'address_4'),
            ('optevia_TownCity', 'address_town'),
            ('optevia_StateCounty', 'address_county'),
            ('optevia_PostCode', 'address_postcode'),
            ('ParentCustomerId.Id', 'company_id'),
            ('optevia_Country.Id', 'address_country_id'),
            ('optevia_Title.Id', 'title_id'),
        ),
        concat=(
            (('optevia_AreaCode', 'optevia_TelephoneNumber'), 'telephone_number', 'optevia_TelephoneNumber'),  # noqa: E501
            (('FirstName', 'MiddleName'), 'first_name', 'FirstName'),
        ),
        undef=('title_id', 'company_id'),
    ),
    Mapping(
        from_entitytype='detica_interactionSet', ToModel=interaction.Interaction,
        fields=(
            ('ActivityId', 'id'),
            ('Subject', 'subject'),
            ('optevia_Notes', 'notes'),
            ('optevia_InteractionCommunicationChannel.Id', 'interaction_type_id'),
            ('optevia_Advisor.Id', 'dit_advisor_id'),
            ('optevia_Contact.Id', 'contact_id'),
            ('optevia_Organisation.Id', 'company_id'),
            ('optevia_ServiceProvider.Id', 'dit_team_id'),
            ('optevia_Service.Id', 'service_id'),
        ),
        undef=(
            'company_id',
            'contact_id',
            'service_id',
            'dit_advisor_id',
            'dit_team_id',
            'interaction_type_id',
        ),
    ),
    Mapping(
        from_entitytype='optevia_servicedeliverySet',
        ToModel=interaction.ServiceDelivery,
        fields=(
            ('optevia_servicedeliveryId', 'id'),
            ('optevia_Notes', 'notes'),
            ('optevia_CustomerCommentFeedback', 'feedback'),
            ('optevia_ServiceDeliveryStatus.Id', 'status_id'),
            ('optevia_ServiceOffer.Id', 'service_offer_id'),
            ('optevia_Service.Id', 'service_id'),
            ('optevia_ServiceProvider.Id', 'dit_team_id'),
            ('optevia_Organisation.Id', 'company_id'),
            ('optevia_Contact.Id', 'contact_id'),
            ('optevia_Advisor.Id', 'dit_advisor_id'),
            ('optevia_UKRegion.Id', 'uk_region_id'),
            ('optevia_Sector.Id', 'sector_id'),
            ('optevia_LeadCountry.Id', 'country_of_interest_id'),
        ),
        undef=(
            'company_id',
            'contact_id',
            'service_id',
            'dit_advisor_id',
            'dit_team_id',
        ),
    ),
    Mapping(
        from_entitytype='optevia_serviceofferSet',
        ToModel=interaction.ServiceOffer,
        fields=(
            ('optevia_serviceofferId', 'id'),
            ('optevia_Service.Id', 'service_id'),
            ('optevia_ServiceProvider.Id', 'dit_team_id'),
        ),
    ),
)

def get_mapping(Model):
    return next(filter(lambda m: m.ToModel == Model, mappings))
