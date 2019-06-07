from enum import Enum

from datahub.core.constants import Constant


class ServiceQuestion(Enum):
    """ServiceQuestion."""

    # providing_investment_advice_and_information
    piai_what_did_you_give_advice_about = Constant(
        'What did you give advice about?',
        '3c69f671-0888-475c-97e5-bc55461db35e',
    )

    # providing_investment_advice_and_information
    piai_was_this_of_significant_assistance = Constant(
        'Was this of significant assistance?',
        '638a1771-1529-4b7e-a633-b4f190d78ad2',
    )

    # global_growth_service
    ggs_status = Constant(
        'Status',
        '7360689f-3a9b-4139-b888-265ae1149bff',
    )


class ServiceAnswerOption(Enum):
    """ServiceAnswerOption."""

    # providing_investment_advice_and_information
    piai_banking_and_funding = Constant(
        'Banking & Funding',
        'd7293a68-05a6-461b-911c-2f07b4306c1e',
    )

    piai_dit_or_government_services = Constant(
        'DIT or Government Services',
        'e5f83d7f-f696-4069-b649-a3e295b41046',
    )

    # providing_investment_advice_and_information
    piai_yes = Constant(
        'Yes',
        '4cab6210-c38f-4b3b-935d-f8cad14202f2',
    )

    # global_growth_service
    ggs_completed = Constant(
        'Completed',
        'c091120c-d68b-45c1-9b39-bc58693b4a64',
    )


class ServiceAdditionalQuestion(Enum):
    """ServiceAdditionalQuestion."""

    # global_growth_service
    ggs_completed_grant_offered = Constant(
        'Grant Offered',
        'f3fd9c77-c8ab-4806-b769-847cc57346a1',
    )
    # global_growth_service
    ggs_completed_net_receipt = Constant(
        'Net Receipt',
        'c6c8b7b2-9015-46c5-b145-c8b2865919db',
    )
