from enum import Enum

from datahub.core.constants import Constant


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
    """Level of Involvemnet constants."""

    no_involvement = Constant('No Involvement', '945f13e9-9a27-4921-8d2d-8daf5a4c59a8')
    hq_and_post_only = Constant('HQ and Post Only', 'bb68ba20-ef54-472d-9a1e-309c1eaa79c4')
    post_only = Constant('Post Only', '1a01c63b-26ad-46eb-b8aa-c925c2395ec9')
    hq_only = Constant('HQ Only', '9c22137d-648e-4ecb-8fe7-652ac6a4f53a')
