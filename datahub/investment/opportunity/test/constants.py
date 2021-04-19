from enum import Enum

from datahub.core.constants import Constant


class AbandonmentReason(Enum):
    """Opportunity abandonment reason constants."""

    promoter_abandoned_the_opportunity = Constant(
        'Promoter(s) abandoned the opportunity',
        '3a38ccff-69c5-40b0-af54-3426ad94e2cb',
    )


class OpportunityStatus(Enum):
    """Opportunity status constants."""

    seeking_investment = Constant(
        'Seeking investment',
        '1386d4f4-732d-44b9-af8e-dffe7dd07d7b',
    )
    abandoned = Constant(
        'Abandoned',
        'c14547fb-a8ee-410b-a144-06c882167a41',
    )


class OpportunityType(Enum):
    """Opportunity type constants."""

    large_capital = Constant(
        'Large capital',
        'c064e66a-a6bc-4ad6-9a88-0bdd69519f55',
    )


class OpportunityValueType(Enum):
    """Opportunity value type constants."""

    capital_expenditure = Constant(
        'Capital expenditure',
        '496379ec-7cd2-4746-98f7-143c905dd6aa',
    )
    gross_development_value = Constant(
        'Gross development value (GDV)',
        'edeff484-2bd1-40e6-94ca-0437d6115886',
    )


class SourceOfFunding(Enum):
    """Opportunity source of funding constants."""

    international = Constant(
        'International',
        '35cd0c71-5051-4e01-a609-09bb06f3039b',
    )
