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

    pass


class Event(BaseConstantModel):
    """Event."""

    pass


class HeadquarterType(BaseConstantModel):
    """Head Quarter."""

    pass


class CompanyClassification(BaseConstantModel):
    """Company classification."""

    pass
