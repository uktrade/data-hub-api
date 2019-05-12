from datahub.core.utils import StrEnum


class InvestorProfilePermission(StrEnum):
    """Permission codename constants."""

    view_investor_profile = 'view_largecapitalinvestorprofile'
    export = 'export_largecapitalinvestorprofile'
