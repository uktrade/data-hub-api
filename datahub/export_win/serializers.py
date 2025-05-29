from datetime import datetime

import reversion
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext_lazy
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import (
    BooleanField,
    CharField,
    DateTimeField,
    ModelSerializer,
    SerializerMethodField,
)

from datahub.company.models import Company, CompanyExport, Contact, ExportExperience
from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.core.utils import get_financial_year
from datahub.export_win.models import (
    HVC,
    AssociatedProgramme,
    Breakdown,
    BreakdownType,
    BusinessPotential,
    CustomerResponse,
    CustomerResponseToken,
    ExpectedValueRelation,
    Experience,
    HQTeamRegionOrPost,
    HVOProgrammes,
    MarketingSource,
    Rating,
    SupportType,
    TeamType,
    Win,
    WinAdviser,
    WinType,
    WinUKRegion,
    WithoutOurSupport,
)
from datahub.export_win.tasks import (
    create_token_for_contact,
    get_all_fields_for_client_email_receipt,
    get_all_fields_for_lead_officer_email_receipt_no,
    get_all_fields_for_lead_officer_email_receipt_yes,
    notify_export_win_email_by_rq_email,
    update_customer_response_for_lead_officer_notification_id,
    update_customer_response_token_for_email_notification_id,
)
from datahub.export_win.validators import (
    DataConfirmedValidator,
    DuplicateContributingAdviserValidator,
    DuplicateTeamMemberValidator,
    LeadOfficerAndContributingAdviserValidator,
    LeadOfficerAndTeamMemberValidator,
    TeamMembersAndContributingAdvisersValidator,
)
from datahub.metadata.models import Country, Sector


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


class LegacyBreakdownSerializer(ModelSerializer):
    """Breakdown serializer for legacy win view."""

    year = SerializerMethodField()

    def get_year(self, breakdown):
        return get_financial_year(
            breakdown.win.date + relativedelta(years=breakdown.year - 1),
        )

    class Meta:
        model = Breakdown
        fields = (
            'year',
            'value',
        )


class WinAdviserSerializer(ModelSerializer):
    """Win adviser serialiser."""

    adviser = NestedAdviserField()
    team_type = NestedRelatedField(TeamType)
    hq_team = NestedRelatedField(HQTeamRegionOrPost)

    # legacy field
    name = CharField(read_only=True)

    class Meta:
        model = WinAdviser
        fields = (
            'id',
            'adviser',
            # legacy field
            'name',
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
    responded_on = DateTimeField(read_only=True)

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
            'interventions_were_prerequisite',
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
            'responded_on',
        )


class LegacyCustomerResponseSerializer(ModelSerializer):
    """Serializer for CustomerResponse to expose confirmation status and date."""

    confirmed = BooleanField(source='agree_with_win', read_only=True)
    date = DateTimeField(source='responded_on', read_only=True)

    class Meta:
        model = CustomerResponse
        fields = (
            'confirmed',
            'date',
        )
        read_only_fields = fields


class WinSerializer(ModelSerializer):
    """Win serializer."""

    default_error_messages = {
        'cannot_change_win': gettext_lazy(
            'A win cannot be changed by contributing advisers.',
        ),
    }

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
    customer_location = NestedRelatedField(WinUKRegion)
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
    # TODO: advisers should be removed once front end starts using contributing_advisers
    advisers = WinAdviserSerializer(many=True, required=False)
    contributing_advisers = WinAdviserSerializer(many=True, required=False, source='advisers')

    breakdowns = BreakdownSerializer(many=True)

    complete = BooleanField(read_only=True)
    first_sent = DateTimeField(read_only=True)
    last_sent = DateTimeField(read_only=True)

    migrated_on = DateTimeField(read_only=True)

    # legacy fields
    company_name = CharField(read_only=True)
    customer_name = CharField(read_only=True)
    customer_job_title = CharField(read_only=True)
    customer_email_address = CharField(read_only=True)
    lead_officer_name = CharField(read_only=True)
    lead_officer_email_address = CharField(read_only=True)
    adviser_name = CharField(read_only=True)
    adviser_email_address = CharField(read_only=True)

    company_export = NestedRelatedField(
        CompanyExport,
        extra_fields=('title',),
        required=False,
    )

    class Meta:
        model = Win
        fields = (
            'id',
            'adviser',
            # legacy field
            'adviser_name',
            # legacy field
            'adviser_email_address',
            'advisers',
            'contributing_advisers',
            'breakdowns',
            'company',
            # legacy field
            'company_name',
            'company_contacts',
            # legacy field
            'customer_name',
            # legacy field
            'customer_job_title',
            # legacy field
            'customer_email_address',
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
            # legacy field
            'lead_officer_name',
            # legacy field
            'lead_officer_email_address',
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
            'company_export',
            'first_sent',
            'last_sent',
            'migrated_on',
        )
        validators = [
            DuplicateContributingAdviserValidator(),
            DuplicateTeamMemberValidator(),
            LeadOfficerAndContributingAdviserValidator(),
            LeadOfficerAndTeamMemberValidator(),
            TeamMembersAndContributingAdvisersValidator(),
            DataConfirmedValidator(),
        ]

    def create(self, validated_data):
        """Create win, corresponding breakdowns and advisers."""
        breakdowns = validated_data.pop('breakdowns')
        advisers = validated_data.pop('advisers', [])
        contributing_advisers = validated_data.pop('contributing_advisers', [])
        if contributing_advisers:
            advisers = contributing_advisers
        company_contacts = validated_data.pop('company_contacts')
        type_of_support = validated_data.pop('type_of_support')
        associated_programme = validated_data.pop('associated_programme')
        team_members = validated_data.pop('team_members', [])
        with transaction.atomic(), reversion.create_revision():
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
                notify_export_win_email_by_rq_email(
                    company_contact.email,
                    template_id,
                    context,
                    update_customer_response_token_for_email_notification_id,
                    token.id,
                )
            reversion.set_comment('Win created')
        return win

    def update(self, instance, validated_data):
        """Update win, corresponding breakdowns and advisers."""
        self._self_check_for_contributing_adviser(instance)

        # adviser should never be updated
        validated_data.pop('adviser', None)

        breakdowns = validated_data.pop('breakdowns', None)
        advisers = validated_data.pop('advisers', None) or validated_data.pop(
            'contributing_advisers',
            None,
        )
        company_contacts = validated_data.pop('company_contacts', None)
        type_of_support = validated_data.pop('type_of_support', None)
        associated_programme = validated_data.pop('associated_programme', None)
        team_members = validated_data.pop('team_members', None)
        with transaction.atomic(), reversion.create_revision():
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
            reversion.set_comment('Win updated')
        return instance

    def _self_check_for_contributing_adviser(self, instance):
        """Checks if request is made by contributing adviser."""
        request = self.context.get('request')
        user = request.user if request else None
        if user and user.id in instance.advisers.values_list('adviser_id', flat=True):
            raise PermissionDenied(self.default_error_messages['cannot_change_win'])


class LimitedExportWinSerializer(ModelSerializer):
    """Limited export win serializer."""

    country = NestedRelatedField(Country)
    goods_vs_services = NestedRelatedField(ExpectedValueRelation)
    export_experience = NestedRelatedField(ExportExperience)
    lead_officer = NestedAdviserField()
    breakdowns = BreakdownSerializer(many=True)

    class Meta:
        model = Win
        fields = (
            'date',
            'country',
            'goods_vs_services',
            'export_experience',
            'lead_officer',
            'breakdowns',
            'description',
        )


class PublicCustomerResponseSerializer(ModelSerializer):
    """Public customer response serializer."""

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
    company_contact = SerializerMethodField()

    def get_company_contact(self, obj):
        token = self.context.get('token')
        field = NestedRelatedField(
            Contact,
            extra_fields=(
                'name',
                'email',
            ),
        )
        return field.to_representation(token.company_contact)

    def update(self, instance, validated_data):
        """Update the customer response and invalidate token."""
        with transaction.atomic():
            instance = super().update(instance, validated_data)

            instance.responded_on = datetime.utcnow()
            instance.save(update_fields=('responded_on',))

            CustomerResponseToken.objects.filter(
                id=self.context.get('token_pk'),
            ).update(
                expires_on=datetime.utcnow(),
            )

        if instance.agree_with_win:
            template_id = settings.EXPORT_WIN_LEAD_OFFICER_APPROVED_TEMPLATE_ID
            context = get_all_fields_for_lead_officer_email_receipt_yes(instance)
        else:
            template_id = settings.EXPORT_WIN_LEAD_OFFICER_REJECTED_TEMPLATE_ID
            context = get_all_fields_for_lead_officer_email_receipt_no(instance)

        notify_export_win_email_by_rq_email(
            instance.win.lead_officer.contact_email,
            template_id,
            context,
            update_customer_response_for_lead_officer_notification_id,
            instance.id,
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
            'company_contact',
        )


class DataHubLegacyExportWinSerializer(ModelSerializer):
    """Legacy read-only serialiser for export win views."""

    response = SerializerMethodField(read_only=True)

    title = CharField(source='name_of_export', read_only=True)
    customer = CharField(source='company_name', read_only=True)
    hvc = SerializerMethodField(read_only=True)
    # TODO: officer field should be removed once FE is updated to use lead_officer field
    officer = SerializerMethodField(read_only=True)
    lead_officer = SerializerMethodField(read_only=True)
    country = SerializerMethodField(read_only=True)
    sector = SerializerMethodField(read_only=True)
    contact = SerializerMethodField(read_only=True)
    created = SerializerMethodField(read_only=True)
    value = SerializerMethodField(read_only=True)
    business_potential = SerializerMethodField(read_only=True)
    adviser = SerializerMethodField(read_only=True)
    team_members = NestedAdviserField(many=True, required=False)
    contributing_advisers = WinAdviserSerializer(many=True, required=False, source='advisers')

    def get_created(self, win):
        return win.created_on

    def get_value(self, win):
        """Return breakdown vaules in a value nested dict.
        Use only breakdown type EXPORT.
        """
        breakdowns_exports = win.breakdowns.filter(type__name='Export')
        breakdowns = LegacyBreakdownSerializer(breakdowns_exports, many=True)
        return {
            'export': {
                'total': win.total_expected_export_value,
                'breakdowns': breakdowns.data,
            },
        }

    def get_officer(self, win):
        return self.get_lead_officer(win)

    def get_lead_officer(self, win):
        """Return lead officer in a officer nested dict."""
        if win.lead_officer:
            officer = {
                'id': win.lead_officer.id,
                'name': win.lead_officer.name,
                'email': win.lead_officer.contact_email,
            }
        else:
            officer = {
                'name': win.lead_officer_name,
                'email': win.lead_officer_email_address,
            }
        officer.update(
            {
                'team': {
                    'type': win.team_type.name,
                    'sub_type': win.hq_team.name,
                },
            },
        )
        return officer

    def get_adviser(self, win):
        """Return adviser in a nested dict."""
        if win.adviser:
            adviser = {
                'id': win.adviser.id,
                'name': win.adviser.name,
                'email': win.adviser.contact_email,
            }
        else:
            adviser = {
                'name': win.adviser_name,
                'email': win.adviser_email_address,
            }
        return adviser

    def get_hvc(self, win):
        """Return hvc data in a hvc nested dict."""
        if win.hvc:
            return {
                'code': win.hvc.campaign_id,
                'name': win.hvc.name,
            }
        return None

    def get_contact(self, win):
        """Return contact information in a contact nested dict."""
        contact = win.company_contacts.first()
        if contact:
            return {
                'id': contact.id,
                'name': contact.name,
                'email': contact.email,
                'job_title': contact.job_title,
            }
        return {
            'name': win.customer_name,
            'email': win.customer_email_address,
            'job_title': win.customer_job_title,
        }

    def get_country(self, win):
        """Return country name for the code."""
        if win.country:
            return win.country.name
        return None

    def get_sector(self, win):
        """Return sector name for the code."""
        if win.sector:
            return win.sector.name
        return None

    def get_business_potential(self, win):
        """Return human readable name for business type."""
        if win.business_potential:
            return win.business_potential.name
        return None

    def get_response(self, win):
        if win.customer_response.responded_on:
            return LegacyCustomerResponseSerializer(
                win.customer_response,
            ).data
        return None

    class Meta:
        model = Win
        fields = (
            'id',
            'adviser',
            'title',
            'date',
            'created',
            'country',
            'sector',
            'business_potential',
            'business_type',
            'name_of_export',
            'officer',
            'lead_officer',
            'contact',
            'value',
            'customer',
            'response',
            'hvc',
            'team_members',
            'contributing_advisers',
        )
        read_only_fields = fields
