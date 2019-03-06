from enum import Enum

from datahub.core.constants import Constant


FEATURE_FLAG_STREAMLINED_FLOW = 'streamlined-investment-flow'


class SpecificProgramme(Enum):
    """Specific Investment Programme constants."""

    innovation_gateway = Constant('Innovation Gateway', '8803a907-a9be-4fce-9482-b9bd3dece344')
    space = Constant('Space', '1c91dd94-cae4-4ea4-b37e-8ef88cb10e7f')
    advanced_engineering_supply_chain = Constant(
        'Advanced Engineering Supply Chain',
        '6513f918-4263-4516-8abb-8e4a6a4de857',
    )


class InvestorType(Enum):
    """Investor Type constants."""

    new_investor = Constant('New Investor', 'e6a01052-8c36-4a32-b5b9-fc2be4b34408')
    existing_investor = Constant('Existing Investor', '40e33f91-f565-4b89-8e18-cfefae192245')


class Involvement(Enum):
    """Level of Involvement constants."""

    no_involvement = Constant('No Involvement', '945f13e9-9a27-4921-8d2d-8daf5a4c59a8')
    hq_and_post_only = Constant('HQ and Post Only', 'bb68ba20-ef54-472d-9a1e-309c1eaa79c4')
    post_only = Constant('Post Only', '1a01c63b-26ad-46eb-b8aa-c925c2395ec9')
    hq_only = Constant('HQ Only', '9c22137d-648e-4ecb-8fe7-652ac6a4f53a')


class LikelihoodToLand(Enum):
    """Likelihood to land constants."""

    low = Constant('Low', 'b3515282-dc36-487a-a5af-320cde165575')
    medium = Constant('Medium', '683ca57b-bd69-462c-852f-d2177e35b2eb')
    high = Constant('High', '90531272-fc9c-4403-9320-b69e51fbec06')


class ProjectManagerRequestStatus(Enum):
    """Project manager request status constants."""

    requested = Constant('Requested', '1fcebb43-244f-47e7-81f8-97790afa6383')
    rejected = Constant('Rejected', 'ad60c3ba-03d5-47de-b31f-a9f5ad1bc220')
    assigned = Constant('Assigned', '9fc09623-f84f-450e-994b-3234c6d3248c')
    re_requested = Constant('Re-requested', '993f31d9-549d-4c0d-95f0-0f86e62e949d')
    self_assigned = Constant('Self assigned', 'd50b8f0c-20c1-484e-9018-b98e9631b08b')


class InvestmentActivityType(Enum):
    """Investment Activity type constants."""

    change = Constant('Change', '931f96a9-bd15-49c0-b8ee-ab3ad7ff27b2')
    risk = Constant('Risk', '9810a38f-95f6-4cb4-87f4-369eef23d2ca')
    issue = Constant('Issue', '6aa82e79-bfab-4466-8d92-e108fd4c0b42')
    spi_interaction = Constant('SPI Interaction', 'fa6ed4db-4e1d-4903-988b-3e8be45b37c2')
    internal_interaction = Constant('Internal Interaction', 'c50d2f7a-57cd-435e-bf87-d04c1dab11e6')
