from enum import Enum

from datahub.core.constants import Constant


class ProfileType(Enum):
    """Specific profile type constants."""

    large = Constant(
        'Large',
        '32451551-28d9-4aff-bc25-45e4cfb15265',
    )
    growth = Constant(
        'Growth',
        '38a38617-84d9-41d0-bf01-d8f027cd109b',
    )
