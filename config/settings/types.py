"""
This module contains types that are used in the config package.

They are defined here rather than in `datahub` to avoid circular imports
between `config` and `datahub`.
"""

from enum import auto, Enum


class HawkScope(Enum):
    """Scopes used for Hawk views."""
    activity_stream = auto()
    public_company = auto()
    data_flow_api = auto()
    metadata = auto()
    public_omis = auto()
