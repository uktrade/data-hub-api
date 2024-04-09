from datahub.company.models.adviser import Advisor
from datahub.company.models.company import Company
from datahub.company.models.contact import Contact
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    ContactFactory,
)
from datahub.event.models import Event
from datahub.event.test.factories import EventFactory
from datahub.interaction.models import Interaction
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    InvestmentProjectInteractionFactory,
)
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.omis.order.models import Order
from datahub.omis.order.test.factories import OrderFactory


MODEL_INFO = {
    'adviser': {
        'factories': [AdviserFactory],
        'model': Advisor,
        'table_name': 'company_advisor',
        'target_number': 18000,
    },
    'company': {
        'factories': [CompanyFactory],
        'model': Company,
        'table_name': 'company_company',
        'target_number': 510000,
    },
    'contact': {
        'factories': [ContactFactory],
        'model': Contact,
        'table_name': 'company_contact',
        'target_number': 950000,
    },
    'event': {
        'factories': [EventFactory],
        'model': Event,
        'table_name': 'company_contact',
        'target_number': 37000,
    },
    'interaction': {
        'factories': [
            CompanyInteractionFactory,
            InvestmentProjectInteractionFactory,
        ],
        'model': Interaction,
        'table_name': 'interaction_interaction',
        'target_number': 4000000,
    },
    'investment': {
        'factories': [InvestmentProjectFactory],
        'model': InvestmentProject,
        'table_name': 'investment_investmentproject',
        'target_number': 85000,
    },
    'order': {
        'factories': [OrderFactory],
        'model': Order,
        'table_name': 'order_order',
        'target_number': 32000,
    },
}
