from datahub.core.constants import InvestmentProjectStage


def test_investment_project_stage_get_by_id():
    """
    It should be possible to get a project stage by its uuid.
    """
    assign_pm_id = 'c9864359-fb1a-4646-a4c1-97d10189fc03'
    investment_project_stage = InvestmentProjectStage.get_by_id(assign_pm_id)
    assert isinstance(investment_project_stage, InvestmentProjectStage)
    assert investment_project_stage.name == 'assign_pm'
