from datetime import datetime

from logging import getLogger

from dateutil.parser import parse

from django.db.models import Q

from datahub.company.models import (
    Advisor,
    Contact,
    ExportExperience,
)
from datahub.core.utils import get_financial_year
from datahub.export_win.export_wins_api import get_legacy_export_wins_dataset
from datahub.export_win.models import (
    AssociatedProgramme,
    Breakdown,
    BreakdownType,
    BusinessPotential,
    CustomerResponse,
    ExpectedValueRelation,
    Experience,
    HQTeamRegionOrPost,
    HVC,
    HVOProgrammes,
    LegacyExportWinsToDataHubCompany,
    MarketingSource,
    Rating,
    SupportType,
    TeamType,
    Win,
    WinAdviser,
    WinUKRegion,
    WithoutOurSupport,
)
from datahub.export_win.utils import calculate_totals_for_export_win
from datahub.metadata.models import (
    Country,
    Sector,
)
from datahub.metadata.query_utils import get_sector_name_subquery


logger = getLogger(__name__)


def create_customer_response_from_legacy(win, item):
    must_resolvers = {
        'access_to_contacts': resolve_legacy_field(
            Rating,
            'confirmation__access_to_contacts',
        ),
        'access_to_information': resolve_legacy_field(
            Rating,
            'confirmation__access_to_information',
        ),
        'developed_relationships': resolve_legacy_field(
            Rating,
            'confirmation__developed_relationships',
        ),
        'gained_confidence': resolve_legacy_field(
            Rating,
            'confirmation__gained_confidence',
        ),
        'improved_profile': resolve_legacy_field(
            Rating,
            'confirmation__improved_profile',
        ),
        'our_support': resolve_legacy_field(
            Rating,
            'confirmation__our_support',
        ),
        'overcame_problem': resolve_legacy_field(
            Rating,
            'confirmation__overcame_problem',
        ),
        'last_export': resolve_legacy_field(
            Experience,
            'confirmation_last_export',
            'name',
        ),
        'marketing_source': resolve_legacy_field(
            MarketingSource,
            'confirmation_marketing_source',
            'name',
        ),
        'expected_portion_without_help': resolve_legacy_field(
            WithoutOurSupport,
            'confirmation_portion_without_help',
            'name',
        ),
        'confirmation__created': lambda item: {
            'responded_on': item.get('confirmation__created', None),
        },
        'confirmation__comments': lambda item: {
            'comments': item.get('confirmation__comments', '') or '',
        },
        'confirmation__name': lambda item: {
            'name': item.get('confirmation__name', '') or '',
        },
        'confirmation__other_marketing_source': lambda item: {
            'other_marketing_source': item.get(
                'confirmation__other_marketing_source',
                '',
            ) or '',
        },
    }

    field_mappings = {
        'confirmation__agree_with_win': 'agree_with_win',
        'confirmation__case_study_willing': 'case_study_willing',
        'confirmation__company_was_at_risk_of_not_exporting':
            'company_was_at_risk_of_not_exporting',
        'confirmation__has_enabled_expansion_into_existing_market':
            'has_enabled_expansion_into_existing_market',
        'confirmation__has_enabled_expansion_into_new_market':
            'has_enabled_expansion_into_new_market',
        'confirmation__has_explicit_export_plans':
            'has_explicit_export_plans',
        'confirmation__has_increased_exports_as_percent_of_turnover':
            'has_increased_exports_as_percent_of_turnover',
        'confirmation__interventions_were_prerequisite':
            'interventions_were_prerequisite',
        'confirmation__involved_state_enterprise':
            'involved_state_enterprise',
        'confirmation__support_improved_speed':
            'support_improved_speed',
    }

    customer_response = {}

    for field, resolver in must_resolvers.items():
        resolved = resolver(item)
        if isinstance(resolved, dict):
            customer_response.update(resolved)
        else:
            customer_response.update(
                {field: resolved},
            )
    for field, mapping in field_mappings.items():
        value = item.get(field)
        customer_response.update(
            **{mapping: value},
        )

    return customer_response


def create_export_win_from_legacy(item):
    must_resolvers = {
        'associated_programme': resolve_many_to_many(
            AssociatedProgramme,
            'associated_programme_',
            5,
        ),
        'business_potential': resolve_legacy_field(
            BusinessPotential,
            'business_potential',
        ),
        'company': resolve_company,
        'company_contacts': resolve_company_contact,
        'country': resolve_legacy_field(
            Country,
            'country_name',
            'name',
        ),
        'customer_location': resolve_legacy_field(
            WinUKRegion,
            'customer_location',
        ),
        'export_experience': resolve_legacy_field(
            ExportExperience,
            'export_experience_display',
            'name',
        ),
        'goods_vs_services': resolve_legacy_field(
            ExpectedValueRelation,
            'goods_vs_services',
        ),
        'hq_team': resolve_legacy_field(
            HQTeamRegionOrPost,
            'hq_team',
        ),
        'hvc': resolve_legacy_field(
            HVC,
            'hvc',
        ),
        'hvo_programme': resolve_legacy_field(
            HVOProgrammes,
            'hvo_programme',
        ),
        'team_type': resolve_legacy_field(
            TeamType,
            'team_type',
        ),
        'type_of_support': resolve_many_to_many(
            SupportType,
            'type_of_support_',
            3,
        ),
        'sector': resolve_legacy_field(
            Sector,
            'sector_display',
            'name',
            annotate={'name': get_sector_name_subquery()},
        ),
        'adviser': resolve_adviser,
        'lead_officer': resolve_lead_officer,
        'line_manager': resolve_line_manager,
        'migrated_on': lambda item, context: datetime.now(),
        'created_on': lambda item, context: parse(item['created']),
        'audit': lambda item, context: '' if item['audit'] is None else item['audit'],
        'is_deleted': lambda item, context: False if item.get(
            'is_active',
            None,
        ) is None else (not item['is_active']),
    }

    # fields to be copied over directly
    field_mappings = {
        'business_type': 'business_type',
        'cdms_reference': 'cdms_reference',
        'complete': 'complete',
        'date': 'date',
        'description': 'description',
        'has_hvo_specialist_involvement': 'has_hvo_specialist_involvement',
        'is_e_exported': 'is_e_exported',
        'is_line_manager_confirmed': 'is_line_manager_confirmed',
        'is_personally_confirmed': 'is_personally_confirmed',
        'is_prosperity_fund_related': 'is_prosperity_fund_related',
        'name_of_customer': 'name_of_customer',
        'name_of_export': 'name_of_export',
        'other_official_email_address': 'other_official_email_address',
    }

    win = {
        'id': item.get('id'),
    }
    for field, resolver in must_resolvers.items():
        resolved = resolver(item, win)
        if isinstance(resolved, dict):
            win.update(resolved)
        else:
            win.update(
                {field: resolved},
            )
    for field, mapping in field_mappings.items():
        value = item.get(field)
        win.update(
            **{mapping: value},
        )

    return win


def migrate_legacy_win(item):
    customer_response_item = {
        key: item.pop(key)
        for key in list(item.keys()) if key.startswith('confirmation_')
    }

    win_data = create_export_win_from_legacy(item)

    many_to_many_fields = [
        'associated_programme',
        'company_contacts',
        'type_of_support',
    ]
    many_to_many = {
        field: win_data.pop(field)
        for field in many_to_many_fields if field in win_data
    }
    win_id = win_data.pop('id')
    if win_data['country'] is None:
        logger.warning(f'Country not found for {win_id}.')
        return

    win, created = Win.objects.all_wins().update_or_create(
        id=win_id,
        defaults=win_data,
    )
    if not created:
        # The associated models need to be deleted
        # to avoid duplicates when migrating them again
        Breakdown.objects.filter(win_id=win.id).delete()
        WinAdviser.objects.filter(win_id=win.id).delete()
    win.created_on = win_data['created_on']
    win.save()

    for field_name, values in many_to_many.items():
        getattr(win, field_name).set(values)
    customer_response_data = create_customer_response_from_legacy(
        win,
        customer_response_item,
    )
    customer_response, _ = CustomerResponse.objects.all_customer_responses().update_or_create(
        win_id=win_id,
        defaults=customer_response_data,
    )
    customer_response.created_on = win_data['created_on']
    customer_response.save()
    return win


def create_breakdown_from_legacy(item):
    win = Win.objects.all_wins().get(id=item['win__id'])
    breakdown_type = BreakdownType.objects.get(export_win_id=item['type'])
    year = item['year'] - get_financial_year(win.date) + 1
    return {
        'win': win,
        'type': breakdown_type,
        'year': year,
        'value': int(item['value']),
    }


def migrate_legacy_win_breakdown(item):
    """Create breakdown from item."""
    breakdown_data = create_breakdown_from_legacy(item)
    if not breakdown_data:
        return None

    breakdown = Breakdown(**breakdown_data)
    breakdown.save()
    return breakdown


def update_legacy_win_totals():
    updated = 0
    for win in Win.objects.filter(migrated_on__isnull=False):
        calc_total = calculate_totals_for_export_win(win)
        win.total_expected_export_value = calc_total['total_export_value']
        win.total_expected_non_export_value = calc_total['total_non_export_value']
        win.total_expected_odi_value = calc_total['total_odi_value']
        win.save()
        updated += 1
    return updated


def create_win_adviser_from_legacy(item):
    hq_team = HQTeamRegionOrPost.objects.get(export_win_id=item['hq_team'])
    team_type = TeamType.objects.get(export_win_id=item['team_type'])

    adviser_data = {
        'win_id': item['win__id'],
        'hq_team': hq_team,
        'team_type': team_type,
        'location': item['location'],
    }

    parts = item.get('name').split()
    # In case name is written as "Joe M. Doe"
    first_name = parts[0]
    last_name = parts[-1]
    adviser = Advisor.objects.filter(
        first_name__iexact=first_name.strip(),
        last_name__iexact=last_name.strip(),
        is_active=True,
    ).order_by('-date_joined').first()
    if adviser:
        adviser_data.update({
            'adviser': adviser,
        })
    else:
        adviser_data.update({
            'name': item['name'],
        })
    return adviser_data


def migrate_legacy_win_adviser(item):
    """Create win adviser from item."""
    adviser_data = create_win_adviser_from_legacy(item)
    if not adviser_data:
        return None

    adviser = WinAdviser(**adviser_data)
    adviser.save()
    return adviser


def resolve_legacy_field(model, source_field_name, lookup_field=None, annotate=None, remap=None):
    if not lookup_field:
        lookup_field = 'export_win_id'
    if not annotate:
        annotate = {}
    if not remap:
        remap = {}

    def resolver(data, context=None):
        _field_value = data.get(source_field_name)
        if _field_value == '':
            return None
        field_value = remap.get(_field_value, _field_value)
        try:
            obj = model.objects.annotate(**annotate).get(**{lookup_field: field_value})
            return obj
        except model.DoesNotExist:
            return None
    return resolver


def resolve_many_to_many(model, source_field_name, max_items):
    def resolver(data, context=None):
        resolvers = [
            resolve_legacy_field(model, f'{source_field_name}{i}')
            for i in range(1, max_items + 1)
        ]
        objs = [
            obj for obj in (
                _resolver(data) for _resolver in resolvers
            ) if obj
        ]

        return objs
    return resolver


def resolve_company(data, context=None):
    try:
        mapping = LegacyExportWinsToDataHubCompany.objects.get(
            id=data.get('id'),
        )
        return mapping.company
    except LegacyExportWinsToDataHubCompany.DoesNotExist:
        return {
            'company_name': data.get('company_name'),
        }


def resolve_adviser(data, context=None):
    email = data.get('user__email').strip()
    adviser = Advisor.objects.filter(
        Q(contact_email__iexact=email) | Q(email__iexact=email),
    ).order_by('-date_joined').first()
    if adviser is None:
        return {
            'adviser_name': data.get('user__name'),
            'adviser_email_address': data.get('user__email'),
        }
    return adviser


def resolve_lead_officer(data, context=None):
    filters = Q()
    email = data.get('lead_officer_email_address').strip()
    if email != '':
        filters = Q(email__iexact=email) | Q(contact_email__iexact=email)
    else:
        parts = data.get('lead_officer_name').split()
        # In case name is written as "Joe M. Doe"
        first_name = parts[0]
        last_name = parts[-1]
        filters = Q(
            first_name__iexact=first_name.strip(),
        ) & Q(
            last_name__iexact=last_name.strip(),
        )
    adviser = Advisor.objects.filter(
        filters,
    ).order_by('-date_joined').first()
    if adviser is None:
        return {
            'lead_officer_name': data.get('lead_officer_name'),
            'lead_officer_email_address': data.get('lead_officer_email_address'),
        }
    return adviser


def resolve_line_manager(data, context=None):
    parts = data.get('line_manager_name').split()
    # In case name is written as "Joe M. Doe"
    first_name = parts[0]
    last_name = parts[-1]
    adviser = Advisor.objects.filter(
        first_name__iexact=first_name.strip(),
        last_name__iexact=last_name.strip(),
    ).order_by('-date_joined').first()
    if adviser is None:
        return {
            'line_manager_name': data.get('line_manager_name'),
        }
    return adviser


def _get_legacy_customer_info(data):
    return {
        'customer_name': data['customer_name'],
        'customer_job_title': data['customer_job_title'],
        'customer_email_address': data['customer_email_address'],
    }


def resolve_company_contact(data, context=None):
    if 'company' in context:
        parts = data['customer_name'].split()
        # In case name is written as "Joe M. Doe"
        first_name = parts[0]
        last_name = parts[-1]
        contact = Contact.objects.filter(
            first_name__iexact=first_name,
            last_name__iexact=last_name,
            company=context['company'],
            transferred_to__isnull=True,
        ).order_by('-created_on').first()
        if contact:
            return {
                'company_contacts': [contact],
            }
    return _get_legacy_customer_info(data)


def migrate_all_legacy_wins():
    wins = 0
    for page in get_legacy_export_wins_dataset('/datasets/data-hub-wins'):
        for legacy_win in page:
            migrate_legacy_win(legacy_win)
            wins += 1

    for page in get_legacy_export_wins_dataset('/datasets/data-hub-breakdowns'):
        for legacy_breakdown in page:
            migrate_legacy_win_breakdown(legacy_breakdown)

    for page in get_legacy_export_wins_dataset('/datasets/data-hub-advisors'):
        for legacy_adviser in page:
            migrate_legacy_win_adviser(legacy_adviser)

    update_legacy_win_totals()

    return wins