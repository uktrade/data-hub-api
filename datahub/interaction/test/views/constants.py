from enum import Enum

from datahub.core.constants import Constant


class ServiceQuestionID(Enum):
    """ServiceQuestion."""

    # providing_investment_advice_and_information
    piai_what_did_you_give_advice_about = '3c69f671-0888-475c-97e5-bc55461db35e'

    making_export_introductions = '054b29fe-c14b-463d-8177-c378d3a819aa'


class ServiceAnswerOptionID(Enum):
    """ServiceAnswerOption."""

    # providing_investment_advice_and_information
    piai_banking_and_funding = 'd7293a68-05a6-461b-911c-2f07b4306c1e'
    piai_dit_or_government_services = 'e5f83d7f-f696-4069-b649-a3e295b41046'

    making_export_introductions_customers = 'a0fabd27-587b-49d1-9e56-eb789b66b7cd'


class TradeAgreement(Enum):
    """Trade agreement constants"""

    uk_australia = Constant(
        'UK-Australia Mutual Recognition Agreement',
        '50370070-71f9-4ada-ae2c-cd0a737ba5e2',
    )
    uk_japan = Constant(
        'UK-Japan Comprehensive Economic Partnership Agreement',
        '05587f64-b976-425e-8763-3557c7936632',
    )
