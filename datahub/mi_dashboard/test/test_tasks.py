from unittest.mock import Mock

import pytest
from django.conf import settings

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

    mi_investment_project_etl_pipeline.apply()

    assert run_mi_investment_project_etl_pipeline_mock.call_count == 1


def test_mi_dashboard_feed_retries_on_error(monkeypatch):
    """Test that the mi_dashboard_feed task retries on error."""
    run_mi_investment_project_etl_pipeline_mock = Mock(side_effect=[AssertionError, (0, 0)])
    monkeypatch.setattr(
        'datahub.mi_dashboard.tasks.run_mi_investment_project_etl_pipeline',
        run_mi_investment_project_etl_pipeline_mock,
    )

    mi_investment_project_etl_pipeline.apply()

    assert run_mi_investment_project_etl_pipeline_mock.call_count == 2


@pytest.mark.parametrize(
    'elapsed_time,num_warnings',
    (
        (settings.MI_FDI_DASHBOARD_TASK_DURATION_WARNING_THRESHOLD + 1, 1),
        (settings.MI_FDI_DASHBOARD_TASK_DURATION_WARNING_THRESHOLD, 0),
    ),
)
def test_mi_dashboard_elapsed_time_warning(elapsed_time, num_warnings, monkeypatch, caplog):
    """Test that crossing the elapsed time threshold would result in warning."""
    caplog.set_level('WARNING')

    run_mi_investment_project_etl_pipeline_mock = Mock(side_effect=[(0, 0)])
    monkeypatch.setattr(
        'datahub.mi_dashboard.tasks.run_mi_investment_project_etl_pipeline',
        run_mi_investment_project_etl_pipeline_mock,
    )

    perf_counter_mock = Mock(side_effect=[0, elapsed_time])
    monkeypatch.setattr(
        'datahub.mi_dashboard.tasks.perf_counter',
        perf_counter_mock,
    )

    mi_investment_project_etl_pipeline.apply()

    assert run_mi_investment_project_etl_pipeline_mock.call_count == 1
    assert len(caplog.records) == num_warnings
    if num_warnings > 0:
        assert (
            'The mi_investment_project_etl_pipeline task took a long time '
            '({elapsed_time:.2f} seconds).'
        ) in caplog.text
