from enum import Enum

from datahub.core.constants import Constant


class OpportunityType(Enum):
    """Opportunity type constants."""

    large_capital = Constant('Large capital', 'c064e66a-a6bc-4ad6-9a88-0bdd69519f55')


class OpportunityStatus(Enum):
    """Opportunity status constants."""

    seeking_investments = Constant('Seeking investments', '1386d4f4-732d-44b9-af8e-dffe7dd07d7b')
