from django.apps import AppConfig


class InvestmentPropositionConfig(AppConfig):
    """
    Configuration class for this app.

    For legacy reasons the label of this application is proposition when
    ideally it should be investment_proposition.
    """

    name = 'datahub.investment.project.proposition'
    label = 'proposition'
