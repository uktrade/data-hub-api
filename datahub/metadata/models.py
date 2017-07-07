from datahub.core.models import BaseConstantModel, BaseOrderedConstantModel


class BusinessType(BaseConstantModel):
    """Company business type."""

    pass


class InteractionType(BaseConstantModel):
    """Interaction type."""

    pass


class Sector(BaseConstantModel):
    """Company sector."""

    pass


class EmployeeRange(BaseOrderedConstantModel):
    """Company employee range."""

    pass


class TurnoverRange(BaseOrderedConstantModel):
    """Company turnover range."""

    pass


class UKRegion(BaseConstantModel):
    """UK region."""

    pass


class Country(BaseConstantModel):
    """Country."""

    class Meta(BaseConstantModel.Meta):  # noqa: D101
        verbose_name_plural = 'countries'


class Title(BaseConstantModel):
    """Contact title."""

    pass


class Role(BaseConstantModel):
    """Contact role."""

    pass


class Team(BaseConstantModel):
    """Team."""

    pass


class Service(BaseConstantModel):
    """Service."""

    pass


class ServiceDeliveryStatus(BaseConstantModel):
    """Service delivery status."""

    class Meta(BaseConstantModel.Meta):  # noqa: D101
        verbose_name_plural = 'service delivery statuses'


class Event(BaseConstantModel):
    """Event."""

    pass


class HeadquarterType(BaseConstantModel):
    """Head Quarter."""

    pass


class CompanyClassification(BaseConstantModel):
    """Company classification."""

    pass


class InvestmentProjectStage(BaseOrderedConstantModel):
    """Investment project stage."""


class InvestmentType(BaseConstantModel):
    """Investment type (for investment projects)."""


class FDIType(BaseConstantModel):
    """Investment type for foreign direct investments (for investment projects)."""


class NonFDIType(BaseConstantModel):
    """Investment type for non-foreign direct investments (for investment projects)."""


class ReferralSourceActivity(BaseConstantModel):
    """Referral source activity type (for investment projects)."""

    class Meta(BaseConstantModel.Meta):  # noqa: D101
        verbose_name_plural = 'referral source activities'


class ReferralSourceWebsite(BaseConstantModel):
    """Referral source website (for investment projects)."""


class ReferralSourceMarketing(BaseConstantModel):
    """Referral source – marketing activities (for investment projects)."""


class InvestmentBusinessActivity(BaseConstantModel):
    """Business activity (for investment projects)."""

    class Meta(BaseConstantModel.Meta):  # noqa: D101
        verbose_name_plural = 'investment business activities'


class InvestmentStrategicDriver(BaseConstantModel):
    """Strategic driver (for investment projects)."""


class SalaryRange(BaseOrderedConstantModel):
    """Salary ranges (used for investment projects)."""
