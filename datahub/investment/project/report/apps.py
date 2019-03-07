from django.apps import AppConfig


class InvestmentReportConfig(AppConfig):
    """
    Configuration class for this app.

    For legacy reasons the label of this application is report when
    ideally it should be investment_report.
    """

    name = 'datahub.investment.project.report'
    label = 'report'
