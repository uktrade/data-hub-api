import pytest
from django.core.exceptions import PermissionDenied

from datahub.admin_report.report import get_report_by_id, get_reports_by_model
from datahub.core.test_utils import create_test_user

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'permission_codenames,expected_result',
    (
        ((), {}),
        (('change_metadatamodel',), {'MetadataModel': ['MetadataReport']}),
    ),
)
def test_get_reports_by_model(permission_codenames, expected_result):
    """Test get_reports_by_model() for various cases."""
    user = create_test_user(permission_codenames=permission_codenames)
    result = get_reports_by_model(user)
    assert {
        model.__name__: [report.__class__.__name__ for report in reports]
        for model, reports in result.items()
    } == expected_result


@pytest.mark.parametrize(
    'permission_codenames,should_raise',
    (
        ((), True),
        (('change_metadatamodel',), False),
    ),
)
def test_get_report_by_id(permission_codenames, should_raise):
    """Test get_report_by_id() for various cases."""
    user = create_test_user(permission_codenames=permission_codenames)

    if should_raise:
        with pytest.raises(PermissionDenied):
            get_report_by_id('test-report', user)
    else:
        assert get_report_by_id('test-report', user)
