import itertools

from datahub.korben.mapping import Mapping, MetadataMapping

import datahub.company.models as company
import datahub.interaction.models as interaction
import datahub.metadata.models as metadata

metadata_specs = (
    (
        'optevia_businesstypeSet',
        metadata.BusinessType,
        'optevia_businesstypeId',
        'optevia_name',
    ),
    (
        'optevia_sectorSet',
        metadata.Sector,
        'optevia_sectorId',
        'optevia_name',
    ),
    (
        'optevia_employeerangeSet',
        metadata.EmployeeRange,
        'optevia_employeerangeId',
        'optevia_name',
    ),
    (
        'optevia_turnoverrangeSet',
        metadata.TurnoverRange,
        'optevia_turnoverrangeId',
        'optevia_name',
    ),
    (
        'optevia_ukregionSet',
        metadata.UKRegion,
        'optevia_ukregionId',
        'optevia_name',
    ),
    (
        'optevia_countrySet',
        metadata.Country,
        'optevia_countryId',
        'optevia_Country',
    ),
    (
        'optevia_titleSet',
        metadata.Title,
        'optevia_titleId',
        'optevia_name',
    ),
    (
        'optevia_contactroleSet',
        metadata.Role,
        'optevia_contactroleId',
        'optevia_name',
    ),
    (
        'optevia_interactioncommunicationchannelSet',
        metadata.InteractionType,
        'optevia_interactioncommunicationchannelId',
        'optevia_name',
    ),
    (
        'BusinessUnitSet',
        metadata.Team,
        'BusinessUnitId',
        'Name',
    ),
    (
        'optevia_serviceSet',
        metadata.Service,
        'optevia_serviceId',
        'optevia_name',
    ),
    (
        'optevia_servicedeliverystatusSet',
        metadata.ServiceDeliveryStatus,
        'optevia_servicedeliverystatusId',
        'optevia_name',
    ),
    (
        'optevia_eventSet',
        metadata.Event,
        'optevia_eventId',
        'optevia_name',
    ),
)

mappings = tuple(itertools.starmap(MetadataMapping, metadata_specs)) + (
    Mapping(
        from_entitytype='AccountSet',
        ToModel=company.Company,
        pk='AccountId',
        fields=(
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
        from_entitytype='SystemUserSet',
        ToModel=company.Advisor,
        pk='SystemUserId',
        fields=(
            ('LastName', 'last_name'),
            ('DomainName', 'email'),
            ('BusinessUnitId.Id', 'dit_team_id'),
        ),
        concat=((('FirstName', 'MiddleName'), 'first_name'),),
    ),
    Mapping(
        from_entitytype='ContactSet',
        ToModel=company.Contact,
        pk='ContactId',
        fields=(
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
            (('optevia_AreaCode', 'optevia_TelephoneNumber'), 'telephone_number'),
            (('FirstName', 'MiddleName'), 'first_name'),
        ),
        undef=('title_id', 'company_id'),
    ),
    Mapping(
        from_entitytype='detica_interactionSet',
        ToModel=interaction.Interaction,
        pk='ActivityId',
        fields=(
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
        pk='optevia_servicedeliveryId',
        fields=(
            ('optevia_Advisor.Id', 'dit_advisor_id'),
            ('optevia_Contact.Id', 'contact_id'),
            ('optevia_Event.Id', 'event_id'),
            ('optevia_LeadCountry.Id', 'country_of_interest_id'),
            ('optevia_Notes', 'notes'),
            ('optevia_Organisation.Id', 'company_id'),
            ('optevia_Sector.Id', 'sector_id'),
            ('optevia_Service.Id', 'service_id'),
            ('optevia_ServiceDeliveryStatus.Id', 'status_id'),
            ('optevia_ServiceOffer.Id', 'service_offer_id'),
            ('optevia_ServiceProvider.Id', 'dit_team_id'),
            ('optevia_UKRegion.Id', 'uk_region_id'),
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
        pk='optevia_serviceofferId',
        fields=(
            ('optevia_Service.Id', 'service_id'),
            ('optevia_ServiceProvider.Id', 'dit_team_id'),
        ),
    ),
    Mapping(
        from_entitytype='optevia_serviceofferSet',
        ToModel=interaction.ServiceOffer,
        pk='optevia_serviceofferId',
        fields=(
            ('optevia_Event.Id', 'event_id'),
            ('optevia_Service.Id', 'service_id'),
            ('optevia_ServiceProvider.Id', 'dit_team_id'),
        ),
    ),
)


def get_mapping(Model):
    try:
        return next(filter(lambda mapping: mapping.ToModel == Model, mappings))
    except StopIteration:
        raise Exception("No mapping for {0}".format(Model))
