from datetime import datetime

from django.conf import settings
from django.db import transaction

from rest_framework.serializers import (
    BooleanField,
    ModelSerializer,
)

from datahub.company.models import Company, Contact, ExportExperience
from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.export_win.models import (
    AssociatedProgramme,
    Breakdown,
    BreakdownType,
    BusinessPotential,
    CustomerResponse,
    CustomerResponseToken,
    ExpectedValueRelation,
    Experience,
    HQTeamRegionOrPost,
    HVC,
    HVOProgrammes,
    MarketingSource,
    Rating,
    SupportType,
    TeamType,
    Win,
    WinAdviser,
    WinType,
    WithoutOurSupport,
)
from datahub.export_win.tasks import (
    create_token_for_contact,
    get_all_fields_for_client_email_receipt,
    notify_export_win_contact_by_rq_email,
    update_customer_response_token_for_email_notification_id,
)
from datahub.metadata.models import Country, Sector, UKRegion


class BreakdownSerializer(ModelSerializer):
    """Breakdown serializer."""

    type = NestedRelatedField(BreakdownType)

    class Meta:
        model = Breakdown
        fields = (
            'id',
            'type',
            'year',
            'value',
        )


class WinAdviserSerializer(ModelSerializer):
    """Win adviser serialiser."""

    adviser = NestedAdviserField()
    team_type = NestedRelatedField(TeamType)
    hq_team = NestedRelatedField(HQTeamRegionOrPost)

    class Meta:
        model = WinAdviser
        fields = (
            'id',
            'adviser',
            'team_type',
            'hq_team',
            'location',
        )


class CustomerResponseSerializer(ModelSerializer):
    """Customer response serializer."""

    our_support = NestedRelatedField(Rating)
    access_to_contacts = NestedRelatedField(Rating)
    access_to_information = NestedRelatedField(Rating)
    improved_profile = NestedRelatedField(Rating)
    gained_confidence = NestedRelatedField(Rating)
    developed_relationships = NestedRelatedField(Rating)
    overcame_problem = NestedRelatedField(Rating)
    expected_portion_without_help = NestedRelatedField(WithoutOurSupport)
    last_export = NestedRelatedField(Experience)
    marketing_source = NestedRelatedField(MarketingSource)

    class Meta:
        model = CustomerResponse
        fields = (
            'id',
            'our_support',
            'access_to_contacts',
            'access_to_information',
            'improved_profile',
            'gained_confidence',
            'developed_relationships',
            'overcame_problem',
            'involved_state_enterprise',
            'support_improved_speed',
            'expected_portion_without_help',
            'last_export',
            'has_enabled_expansion_into_new_market',
            'has_enabled_expansion_into_existing_market',
            'has_increased_exports_as_percent_of_turnover',
            'company_was_at_risk_of_not_exporting',
            'has_explicit_export_plans',
            'agree_with_win',
            'case_study_willing',
            'comments',
            'name',
            'marketing_source',
            'other_marketing_source',
        )


class WinSerializer(ModelSerializer):
    """Win serializer."""

    adviser = NestedAdviserField()
    company = NestedRelatedField(Company)
    company_contacts = NestedRelatedField(
        Contact,
        many=True,
        extra_fields=(
            'name',
            'email',
        ),
    )
    team_members = NestedAdviserField(many=True, required=False)
    customer_location = NestedRelatedField(UKRegion)
    type = NestedRelatedField(WinType, required=False)
    country = NestedRelatedField(Country)
    goods_vs_services = NestedRelatedField(ExpectedValueRelation)
    sector = NestedRelatedField(Sector)
    hvc = NestedRelatedField(HVC, required=False)
    hvo_programme = NestedRelatedField(HVOProgrammes, required=False)
    type_of_support = NestedRelatedField(SupportType, many=True)
    lead_officer = NestedAdviserField()
    team_type = NestedRelatedField(TeamType)
    hq_team = NestedRelatedField(HQTeamRegionOrPost)
    business_potential = NestedRelatedField(BusinessPotential)
    export_experience = NestedRelatedField(ExportExperience)
    associated_programme = NestedRelatedField(AssociatedProgramme, many=True)
    customer_response = CustomerResponseSerializer(read_only=True)
    advisers = WinAdviserSerializer(many=True, required=False)

    breakdowns = BreakdownSerializer(many=True)

    complete = BooleanField(read_only=True)

    class Meta:
        model = Win
        fields = (
            'id',
            'adviser',
            'advisers',
            'breakdowns',
            'company',
            'company_contacts',
            'complete',
            'customer_location',
            'business_type',
            'description',
            'name_of_customer',
            'name_of_customer_confidential',
            'name_of_export',
            'date',
            'country',
            'type',
            'total_expected_export_value',
            'total_expected_non_export_value',
            'total_expected_odi_value',
            'goods_vs_services',
            'sector',
            'is_prosperity_fund_related',
            'hvc',
            'hvo_programme',
            'has_hvo_specialist_involvement',
            'is_e_exported',
            'type_of_support',
            'associated_programme',
            'is_personally_confirmed',
            'is_line_manager_confirmed',
            'lead_officer',
            'team_type',
            'hq_team',
            'business_potential',
            'export_experience',
            'location',
            'created_on',
            'modified_on',
            'complete',
            'customer_response',
            'country',
            'type',
            'export_experience',
            'audit',
            'team_members',
        )

    def create(self, validated_data):
        """Create win, corresponding breakdowns and advisers."""
        breakdowns = validated_data.pop('breakdowns')
        advisers = validated_data.pop('advisers', [])
        company_contacts = validated_data.pop('company_contacts')
        type_of_support = validated_data.pop('type_of_support')
        associated_programme = validated_data.pop('associated_programme')
        team_members = validated_data.pop('team_members', [])
        with transaction.atomic():
            win = Win.objects.create(**validated_data)

            for breakdown in breakdowns:
                Breakdown.objects.create(win=win, **breakdown)

            for win_adviser in advisers:
                WinAdviser.objects.create(win=win, **win_adviser)

            win.company_contacts.set(company_contacts)
            win.type_of_support.set(type_of_support)
            win.associated_programme.set(associated_programme)
            win.team_members.set(team_members)

            customer_response = CustomerResponse.objects.create(
                win=win,
            )
            for company_contact in company_contacts:
                token = create_token_for_contact(
                    company_contact,
                    customer_response,
                )
                context = get_all_fields_for_client_email_receipt(
                    token,
                    customer_response,
                )
                template_id = settings.EXPORT_WIN_CLIENT_RECEIPT_TEMPLATE_ID
                notify_export_win_contact_by_rq_email(
                    company_contact.email,
                    template_id,
                    context,
                    update_customer_response_token_for_email_notification_id,
                    token.id,
                )

        return win

    def update(self, instance, validated_data):
        """Update win, corresponding breakdowns and advisers."""
        breakdowns = validated_data.pop('breakdowns', None)
        advisers = validated_data.pop('advisers', None)
        company_contacts = validated_data.pop('company_contacts', None)
        type_of_support = validated_data.pop('type_of_support', None)
        associated_programme = validated_data.pop('associated_programme', None)
        team_members = validated_data.pop('team_members', None)
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if breakdowns is not None:
                Breakdown.objects.filter(win=instance).delete()
                for breakdown in breakdowns:
                    Breakdown.objects.create(win=instance, **breakdown)

            if advisers is not None:
                WinAdviser.objects.filter(win=instance).delete()
                for win_adviser in advisers:
                    WinAdviser.objects.create(win=instance, **win_adviser)

            if company_contacts is not None:
                instance.company_contacts.set(company_contacts)
            if type_of_support is not None:
                instance.type_of_support.set(type_of_support)
            if associated_programme is not None:
                instance.associated_programme.set(associated_programme)
            if team_members is not None:
                instance.team_members.set(team_members)
        return instance


class LimitedExportWinSerializer(ModelSerializer):
    """Limited export win serializer."""

    country = NestedRelatedField(Country)
    goods_vs_services = NestedRelatedField(ExpectedValueRelation)
    lead_officer = NestedAdviserField()
    breakdowns = BreakdownSerializer(many=True)

    class Meta:
        model = Win
        fields = (
            'date',
            'country',
            'goods_vs_services',
            'lead_officer',
            'breakdowns',
            'description',
        )


class CustomerResponseSerializer(ModelSerializer):
    """Customer response serializer."""

    win = LimitedExportWinSerializer(read_only=True)
    our_support = NestedRelatedField(Rating)
    access_to_contacts = NestedRelatedField(Rating)
    access_to_information = NestedRelatedField(Rating)
    improved_profile = NestedRelatedField(Rating)
    gained_confidence = NestedRelatedField(Rating)
    developed_relationships = NestedRelatedField(Rating)
    overcame_problem = NestedRelatedField(Rating)
    expected_portion_without_help = NestedRelatedField(WithoutOurSupport)
    last_export = NestedRelatedField(Experience)
    marketing_source = NestedRelatedField(MarketingSource)

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update the customer response and invalidate token.
        """
        instance = super().update(instance, validated_data)

        CustomerResponseToken.objects.filter(
            id=self.context.get('token_pk'),
        ).update(
            expires_on=datetime.utcnow(),
        )
        return instance

    class Meta:
        model = CustomerResponse
        fields = (
            'win',
            'agree_with_win',
            'comments',
            'our_support',
            'access_to_contacts',
            'access_to_information',
            'improved_profile',
            'gained_confidence',
            'developed_relationships',
            'overcame_problem',
            'involved_state_enterprise',
            'interventions_were_prerequisite',
            'support_improved_speed',
            'expected_portion_without_help',
            'last_export',
            'company_was_at_risk_of_not_exporting',
            'has_explicit_export_plans',
            'has_enabled_expansion_into_new_market',
            'has_increased_exports_as_percent_of_turnover',
            'has_enabled_expansion_into_existing_market',
            'case_study_willing',
            'marketing_source',
            'other_marketing_source',
        )
