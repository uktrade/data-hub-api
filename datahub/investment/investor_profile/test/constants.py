from enum import Enum

from datahub.core.constants import Constant


class InvestorType(Enum):
    """Investor profile investor type constants."""

    state_pension_fund = Constant(
        'State Pension Fund',
        'ac294431-94ba-4318-9b27-75f0ada99c0d',
    )


class RequiredChecksConducted(Enum):
    """Required checks conducted constants."""

    cleared = Constant(
        'Cleared',
        '02d6fc9b-fbb9-4621-b247-d86f2487898e',
    )


class DealTicketSize(Enum):
    """Deal ticket size constants."""

    up_to_forty_nine_million = Constant(
        'Up to £49 million',
        '56492c50-aa12-404d-a14e-1eaae24ac6ee',
    )


class LargeCapitalInvestmentTypes(Enum):
    """Investment types for large capital constants."""

    direct_investment_in_project_equity = Constant(
        'Direct Investment in Project Equity',
        '4170d99a-02fc-46ee-8fd4-3fe786717708',
    )


class ReturnRate(Enum):
    """Return rate constants."""

    up_to_five_percent = Constant(
        'Up to 5% IRR',
        '6fec56ba-0be9-4931-bd76-16e11924ec55',
    )


class EquityPercentage(Enum):
    """Equity percentage (ranges) constants."""

    zero_percent = Constant(
        '0% - Not required',
        '414a13f7-1b6f-4071-a6d3-d22ed64f4612',
    )


class TimeHorizon(Enum):
    """Time horizon (ranges) constants."""

    up_to_five_years = Constant(
        'Up to 5 years',
        'd2d1bdbb-c42a-459c-adaa-fce45ce08cc9',
    )
    five_to_nine_years = Constant(
        '5-9 years',
        'd186343f-ed66-47e4-9ab0-258f583ff3cb',
    )


class ConstructionRisk(Enum):
    """Construction risk constants."""

    greenfield = Constant(
        'Greenfield (construction risk)',
        '79cc3963-9376-4771-9cba-c1b3cc0ade33',
    )
    brownfield = Constant(
        'Brownfield (some construction risk)',
        '884deaf6-cb0c-4036-b78c-efd92cb10098',
    )


class DesiredDealRole(Enum):
    """Desired deal role constants."""

    lead_manager = Constant(
        'Lead manager / deal structure',
        'efadc6bb-2a73-4627-8ce3-9dc2c34c3f31',
    )
    co_leader_manager = Constant(
        'Co-lead manager',
        '29d930e6-de2f-403d-87dc-764bc418d33a',
    )


class Restriction(Enum):
    """Restriction constants."""

    liquidity = Constant(
        'Liquidity / exchange listing',
        '5b4f5dc5-c836-4572-afd2-013776ed00c5',
    )

    inflation_adjustment = Constant(
        'Inflation adjustment',
        'daa293d4-e18e-44af-b139-bd1b4c4a9067',
    )


class AssetClassInterest(Enum):
    """Asset class interest constants."""

    biofuel = Constant(
        'Biofuel',
        '66507830-595d-432e-8521-9daf11785265',
    )
    biomass = Constant(
        'Biomass',
        'f2b6c1a7-4d4f-4fd9-884b-5e1f5b3525be',
    )
