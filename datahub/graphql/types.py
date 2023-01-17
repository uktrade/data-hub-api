from graphene_django import DjangoObjectType

from datahub.company.models import (
    Advisor,
    Company,
    Contact,
    ExportExperienceCategory,
    OneListTier,
)
from datahub.feature_flag.models import (
    UserFeatureFlag,
    UserFeatureFlagGroup,
)
from datahub.metadata.models import (
    AdministrativeArea,
    BusinessType,
    Country,
    EmployeeRange,
    HeadquarterType,
    OverseasRegion,
    Sector,
    SectorCluster,
    Team,
    TurnoverRange,
    UKRegion,
)


class BaseMetaFields:
    fields = (
        'id',
        'name',
        'disabled_on',
    )


class BusinessTypeGraphQLType(DjangoObjectType):
    class Meta(BaseMetaFields):
        model = BusinessType


class SectorClusterGraphQLType(DjangoObjectType):
    class Meta(BaseMetaFields):
        model = SectorCluster


class EmployeeRangeGraphQLType(DjangoObjectType):
    class Meta(BaseMetaFields):
        model = EmployeeRange


class SectorGraphQLType(DjangoObjectType):
    class Meta:
        model = Sector
        fields = (
            'id',
            'segment',
            'sector_cluster',
            'parent',
        )


class TurnoverRangeGraphQLType(DjangoObjectType):
    class Meta(BaseMetaFields):
        model = TurnoverRange


class UKRegionGraphQLType(DjangoObjectType):
    class Meta(BaseMetaFields):
        model = UKRegion


class OverseasRegionGraphQLType(DjangoObjectType):
    class Meta(BaseMetaFields):
        model = OverseasRegion


class HeadquarterGraphQLType(DjangoObjectType):
    class Meta(BaseMetaFields):
        model = HeadquarterType


class OneListTierGraphQLType(DjangoObjectType):
    class Meta(BaseMetaFields):
        model = OneListTier


class CountryGraphQLType(DjangoObjectType):
    class Meta:
        model = Country
        fields = (
            'id',
            'name',
            'disabled_on',
            'overseas_region',
            'iso_alpha2_code',
        )


class AdministrativeAreaGraphQLType(DjangoObjectType):
    class Meta:
        model = AdministrativeArea
        fields = (
            'id',
            'name',
            'disabled_on',
            'country',
            'area_code',
            'area_name',
        )


class ExportExperienceCategoryGraphQLType(DjangoObjectType):
    class Meta(BaseMetaFields):
        model = ExportExperienceCategory


class CompanyGraphQLType(DjangoObjectType):
    class Meta:
        model = Company
        fields = (
            'id',
            'name',
            'reference_code',
            'company_number',
            'vat_number',
            'duns_number',
            'trading_names',
            'business_type',
            'sector',
            'employee_range',
            'number_of_employees',
            'is_number_of_employees_estimated',
            'turnover_range',
            'turnover',
            'is_turnover_estimated',
            'export_to_countries',
            'future_interest_countries',
            'description',
            'website',
            'uk_region',
            'address_1',
            'address_2',
            'address_town',
            'address_county',
            'address_area',
            'address_country',
            'address_postcode',
            'registered_address_1',
            'registered_address_2',
            'registered_address_town',
            'registered_address_area',
            'registered_address_county',
            'registered_address_country',
            'registered_address_postcode',
            'headquarter_type',
            'one_list_tier',
            'global_headquarters',
            'one_list_account_owner',
            'export_experience_category',
            'archived_documents_url_path',
            'transferred_to',
            'transfer_reason',
            'transferred_on',
            'transferred_by',
            'dnb_investigation_id',
            'pending_dnb_investigation',
            'export_potential',
            'great_profile_status',
            'global_ultimate_duns_number',
            'dnb_modified_on',
            'export_segment',
            'export_sub_segment',
        )


class ContactGraphQLType(DjangoObjectType):
    class Meta:
        model = Contact
        fields = (
            'first_name',
            'last_name',
            'company',
            'full_telephone_number',
        )


class UserFeatureFlagGraphQLType(DjangoObjectType):
    class Meta:
        model = UserFeatureFlag
        fields = (
            'created_on',
            'modified_on',
            'created_by',
            'modified_by',
            'id',
            'code',
            'description',
            'is_active',
        )


class UserFeatureFlagGroupGraphQLType(DjangoObjectType):
    class Meta:
        model = UserFeatureFlagGroup
        fields = (
            'created_on',
            'modified_on',
            'created_by',
            'modified_by',
            'code',
            'features',
            'description',
            'is_active',
        )


class TeamGraphQLType(DjangoObjectType):
    class Meta:
        model = Team
        fields = (
            'disabled_on',
            'id',
            'name',
            'uk_region',
            'country',
            'tags',
        )


class AdvisorGraphQLType(DjangoObjectType):
    class Meta:
        model = Advisor
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'telephone_number',
            'contact_email',
            'dit_team',
            'is_staff',
            'is_active',
            'date_joined',
            'sso_email_user_id',
            'sso_user_id',
            'features',
            'feature_groups',
        )
