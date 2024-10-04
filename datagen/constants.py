from datahub.company.models.adviser import Advisor
from datahub.company.models.company import Company
from datahub.company.models.contact import Contact
from datahub.event.models import Event
from datahub.interaction.models import Interaction
from datahub.investment.project.models import InvestmentProject
from datahub.omis.order.models import Order


MODEL_INFO = {
    'adviser': {
        'model': Advisor,
        'target_number': 18000,
    },
    'company': {
        'model': Company,
        'target_number': 510000,
    },
    'contact': {
        'model': Contact,
        'target_number': 950000,
    },
    'event': {
        'model': Event,
        'target_number': 37000,
    },
    'interaction': {
        'model': Interaction,
        'target_number': 4000000,
    },
    'investment': {
        'model': InvestmentProject,
        'target_number': 85000,
    },
    'order': {
        'model': Order,
        'target_number': 32000,
    },
}
