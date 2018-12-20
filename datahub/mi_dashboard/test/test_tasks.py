from unittest.mock import Mock

import pytest

from datahub.mi_dashboard.tasks import mi_investment_project_etl_pipeline

# mark the whole module for db use
pytestmark = pytest.mark.django_db


def test_mi_dashboard_feed(monkeypatch):
    """Test that the fdi_dashboard_pipeline gets called."""
    run_mi_investment_project_etl_pipeline_mock = Mock(side_effect=[(0, 0)])
    monkeypatch.setattr(
        'datahub.mi_dashboard.tasks.run_mi_investment_project_etl_pipeline',
        run_mi_investment_project_etl_pipeline_mock,
    )

    mi_investment_project_etl_pipeline.apply(args=('2018/2019', ))

    assert run_mi_investment_project_etl_pipeline_mock.call_count == 1


def test_mi_dashboard_feed_retries_on_error(monkeypatch):
    """Test that the mi_dashboard_feed task retries on error."""
    run_mi_investment_project_etl_pipeline_mock = Mock(side_effect=[AssertionError, (0, 0)])
    monkeypatch.setattr(
        'datahub.mi_dashboard.tasks.run_mi_investment_project_etl_pipeline',
        run_mi_investment_project_etl_pipeline_mock,
    )

    mi_investment_project_etl_pipeline.apply(args=('2018/2019', ))

    assert run_mi_investment_project_etl_pipeline_mock.call_count == 2
