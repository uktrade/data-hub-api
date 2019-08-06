from enum import Enum


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
