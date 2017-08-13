from .models import InvestmentProject

from ..apps import SearchApp


class InvestmentSearchApp(SearchApp):
    """SearchApp for investment"""

    name = 'investment'
    ESModel = InvestmentProject
