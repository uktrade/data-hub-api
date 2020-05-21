from datahub.company.constants import OneListTierID
from datahub.company.models import OneListTier
from datahub.core.test_utils import (
    random_obj_for_queryset,
)


def random_non_ita_one_list_tier():
    """Returns random non ITA One List tier."""
    queryset = OneListTier.objects.exclude(
        pk=OneListTierID.tier_d_international_trade_advisers.value,
    )
    return random_obj_for_queryset(queryset)


def format_expected_adviser(adviser):
    """
    Formats Adviser object into format expected to be returned by
    `NestedAdviserWithEmailAndTeamField`.
    """
    if not adviser:
        return None

    return {
        'contact_email': adviser.contact_email,
        'dit_team': {
            'id': str(adviser.dit_team.pk),
            'name': adviser.dit_team.name,
        },
        'id': str(adviser.pk),
        'name': adviser.name,
    }
