from django.contrib.postgres.expressions import ArraySubquery
from django.contrib.postgres.fields import JSONField
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    Count,
    ExpressionWrapper,
    F,
    Func,
    IntegerField,
    Max,
    OuterRef,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import (
    Cast,
    Concat,
    ExtractMonth,
    ExtractYear,
)

from datahub.company.models import Contact
from datahub.dataset.core.views import BaseDatasetView, BaseFilterDatasetView
from datahub.dataset.export_wins import (
    EXPORT_WINS_LEGACY_DATASET_FEATURE_FLAG_NAME,
)
from datahub.dataset.export_wins.pagination import HVCDatasetViewCursorPagination
from datahub.dataset.export_wins.utils import (
    convert_datahub_export_experience_to_export_wins,
    create_columns_with_index,
    use_nulls_on_empty_string_fields,
)

from datahub.export_win.constants import EXPORT_WINS_LEGACY_ID_START_VALUE
from datahub.export_win.models import (
    AssociatedProgramme,
    Breakdown,
    HVC,
    SupportType,
    Win,
    WinAdviser,
)
from datahub.feature_flag.utils import is_feature_flag_active
from datahub.metadata.query_utils import get_sector_name_subquery


class ExportWinsAdvisersDatasetView(BaseDatasetView):
    """
    A GET API view to return export win advisers.
    """

    def get_dataset(self):
        if is_feature_flag_active(
            EXPORT_WINS_LEGACY_DATASET_FEATURE_FLAG_NAME,
        ):
            migrated_filter = {}
        else:
            migrated_filter = {
                'win__migrated_on__isnull': True,
            }
        return (
            WinAdviser.objects.select_related('win', 'adviser', 'hq_team', 'team_type')
            .filter(
                **migrated_filter,
            )
            .values(
                'created_on',
                'win__id',
                'location',
                hq_team_display=F('hq_team__name'),
                team_type_display=F('team_type__name'),
            )
            .annotate(
                id=F('legacy_id'),
                name=Concat(F('adviser__first_name'), Value(' '), F('adviser__last_name')),
                hq_team=F('hq_team__export_win_id'),
                team_type=F('team_type__export_win_id'),
            )
        )


class ExportWinsBreakdownsDatasetView(BaseDatasetView):
    """
    A GET API view to return export win breakdowns.
    """

    def get_dataset(self):
        if is_feature_flag_active(
            EXPORT_WINS_LEGACY_DATASET_FEATURE_FLAG_NAME,
        ):
            migrated_filter = {}
        else:
            migrated_filter = {
                'win__migrated_on__isnull': True,
            }

        return (
            Breakdown.objects.select_related('win', 'breakdown_type')
            .filter(
                **migrated_filter,
            )
            .annotate(
                won_year=ExtractYear('win__date'),
                won_month=ExtractMonth('win__date'),
                provisional_financial_year=Case(
                    When(won_month__gte=4, then=F('won_year')),
                    default=ExpressionWrapper(
                        F('won_year') - 1,
                        output_field=IntegerField(),
                    ),
                    output_field=IntegerField(),
                ),
                financial_year=ExpressionWrapper(
                    F('provisional_financial_year') + (F('year') - 1),
                    output_field=IntegerField(),
                ),
            )
            .values(
                'created_on',
                'win__id',
                'value',
                breakdown_type=F('type__name'),
            )
            .annotate(
                id=F('legacy_id'),
                year=F('financial_year'),
            )
        )


class ExportWinsHVCDatasetView(BaseFilterDatasetView):
    """
    A GET API view to return export win HVCs.
    """

    pagination_class = HVCDatasetViewCursorPagination

    def get_dataset(self, request):
        exclude_legacy = request.query_params.get('exclude_legacy', 'false')
        if is_feature_flag_active(
            EXPORT_WINS_LEGACY_DATASET_FEATURE_FLAG_NAME,
        ):
            exclude_legacy = False

        hvcs = HVC.objects.values(
            'campaign_id',
            'financial_year',
            'name',
        ).annotate(
            id=F('legacy_id'),
        )
        if exclude_legacy == 'true':
            hvcs = hvcs.filter(id__gte=EXPORT_WINS_LEGACY_ID_START_VALUE)
        return hvcs


class ExportWinsWinDatasetView(BaseDatasetView):
    """
    A GET API view to return export win wins.
    """

    def get_dataset(self):
        if is_feature_flag_active(
            EXPORT_WINS_LEGACY_DATASET_FEATURE_FLAG_NAME,
        ):
            migrated_filter = {}
        else:
            migrated_filter = {
                'migrated_on__isnull': True,
            }
        return (
            Win.objects.select_related(
                'adviser',
                'business_potential',
                'country',
                'customer_location',
                'customer_response',
                'export_experience',
                'hvc',
                'hvo_programme',
                'lead_officer',
                'sector',
            )
            .filter(
                **migrated_filter,
            )
            .annotate(
                sector_name=get_sector_name_subquery('sector'),
                # Subquery returns a JSONB document to avoid creating multiple subqueries
                # to retrieve different properties of the same contact
                customer_details=Subquery(
                    Contact.objects.filter(
                        wins=OuterRef('pk'),
                    ).annotate(
                        details=Func(
                            Value('name'), Concat('first_name', Value(' '), 'last_name'),
                            Value('email'), Cast('email', CharField()),
                            Value('job_title'), 'job_title',
                            function='jsonb_build_object',
                        ),
                    ).order_by(
                        'pk',
                    ).values('details')[:1],
                    output_field=JSONField(),
                ),
                temp_cdms_reference=F('cdms_reference'),
                temp_complete=F('complete'),
            )
            .prefetch_related('associated_programme', 'type_of_support')
            .values(
                'created_on',
                'id',
                'audit',
                'business_type',
                'date',
                'description',
                'has_hvo_specialist_involvement',
                'is_e_exported',
                'is_line_manager_confirmed',
                'is_personally_confirmed',
                'is_prosperity_fund_related',
                'line_manager_name',
                'name_of_customer',
                'name_of_export',
                'other_official_email_address',
                'total_expected_export_value',
                'total_expected_non_export_value',
                'total_expected_odi_value',
                created=F('created_on'),
                business_potential_display=F('business_potential__name'),
                confirmation_last_export=F('customer_response__last_export__name'),
                confirmation_marketing_source=F(
                    'customer_response__marketing_source__name',
                ),
                confirmation_portion_without_help=F(
                    'customer_response__expected_portion_without_help__name',
                ),
                country_name=F('country__name'),
                customer_location_display=F('customer_location__name'),
                export_experience_display=F('export_experience__name'),
                goods_vs_services_display=F('goods_vs_services__name'),
                hq_team_display=F('hq_team__name'),
                hvo_programme_display=F('hvo_programme__name'),
                sector_display=F('sector_name'),
                team_type_display=F('team_type__name'),
                num_notifications=Count('customer_response__tokens'),
                customer_email_date=Max('customer_response__tokens__created_on'),
            )
            .annotate(
                complete=Case(
                    When(
                        migrated_on__isnull=True,
                        then=Case(
                            When(num_notifications__gt=0, then=True),
                            default=False,
                            output_field=BooleanField(),
                        ),
                    ),
                    default=F('temp_complete'),
                    output_field=BooleanField(),
                ),
                company_name=F('company__name'),
                confirmation__access_to_contacts=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__our_support__export_win_id'),
                    output_field=IntegerField(),
                ),
                confirmation__access_to_information=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__access_to_information__export_win_id'),
                    output_field=IntegerField(),
                ),
                confirmation__agree_with_win=F('customer_response__agree_with_win'),
                confirmation__case_study_willing=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__case_study_willing'),
                    output_field=BooleanField(),
                ),
                confirmation__comments=F('customer_response__comments'),
                confirmation__company_was_at_risk_of_not_exporting=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__company_was_at_risk_of_not_exporting'),
                    output_field=BooleanField(),
                ),
                confirmation__created=F('customer_response__responded_on'),
                confirmation__developed_relationships=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__developed_relationships__export_win_id'),
                    output_field=IntegerField(),
                ),
                confirmation__gained_confidence=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__gained_confidence__export_win_id'),
                    output_field=IntegerField(),
                ),
                confirmation__has_enabled_expansion_into_existing_market=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__has_enabled_expansion_into_existing_market'),
                    output_field=BooleanField(),
                ),
                confirmation__has_enabled_expansion_into_new_market=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__has_enabled_expansion_into_new_market'),
                    output_field=BooleanField(),
                ),
                confirmation__has_explicit_export_plans=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__has_explicit_export_plans'),
                    output_field=BooleanField(),
                ),
                confirmation__has_increased_exports_as_percent_of_turnover=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__has_increased_exports_as_percent_of_turnover'),
                    output_field=BooleanField(),
                ),
                confirmation__improved_profile=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__improved_profile__export_win_id'),
                    output_field=IntegerField(),
                ),
                confirmation__interventions_were_prerequisite=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__interventions_were_prerequisite'),
                    output_field=BooleanField(),
                ),
                confirmation__involved_state_enterprise=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__involved_state_enterprise'),
                    output_field=BooleanField(),
                ),
                confirmation__name=F('customer_details__name'),
                confirmation__other_marketing_source=F(
                    'customer_response__other_marketing_source',
                ),
                confirmation__our_support=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__our_support__export_win_id'),
                    output_field=IntegerField(),
                ),
                confirmation__overcame_problem=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__overcame_problem__export_win_id'),
                    output_field=IntegerField(),
                ),
                confirmation__support_improved_speed=Case(
                    When(customer_response__responded_on__isnull=True, then=None),
                    default=F('customer_response__support_improved_speed'),
                    output_field=BooleanField(),
                ),
                country=F('country__iso_alpha2_code'),
                hvc=F('hvc__export_win_id'),
                user__email=F('adviser__contact_email'),
                user__name=Concat(
                    'adviser__first_name',
                    Value(' '),
                    'adviser__last_name',
                ),
                lead_officer_email_address=F('lead_officer__contact_email'),
                lead_officer_name=Concat(
                    'lead_officer__first_name',
                    Value(' '),
                    'lead_officer__last_name',
                ),
                associated_programmes=ArraySubquery(
                    AssociatedProgramme.objects.filter(
                        win=OuterRef('pk'),
                    ).order_by('order').values('name'),
                ),
                types_of_support=ArraySubquery(
                    SupportType.objects.filter(
                        win=OuterRef('pk'),
                    ).order_by('order').values('name'),
                ),
                export_wins_export_experience_display=F(
                    'export_experience__export_wins_export_experience__name',
                ),
                customer_email_address=F('customer_details__email'),
                customer_job_title=F('customer_details__job_title'),
                customer_name=F('customer_details__name'),
                cdms_reference=Case(
                    When(
                        temp_cdms_reference='',
                        then=F('company__company_number'),
                    ),
                    default=F('temp_cdms_reference'),
                    output_field=CharField(),
                ),
            )
        )

    def _enrich_data(self, dataset):
        for data in dataset:
            create_columns_with_index(data, 'associated_programmes', 'associated_programme')
            create_columns_with_index(data, 'types_of_support', 'type_of_support')
            use_nulls_on_empty_string_fields(data)
            convert_datahub_export_experience_to_export_wins(data)
