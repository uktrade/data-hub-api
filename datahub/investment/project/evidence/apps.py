from django.apps import AppConfig


class InvestmentEvidenceConfig(AppConfig):
    """
    Configuration class for this app.

    For legacy reasons the label of this application is evidence when
    ideally it should be investment_evidence.
    """

    name = 'datahub.investment.project.evidence'
    label = 'evidence'
