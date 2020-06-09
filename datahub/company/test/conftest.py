import pytest

from datahub.company.models import CompanyPermission
from datahub.core.test_utils import create_test_user


@pytest.fixture
def one_list_editor():
    """An adviser with permission to change one list company."""
    permission_codenames = [
        CompanyPermission.change_company,
        CompanyPermission.change_one_list_tier_and_global_account_manager,
        CompanyPermission.change_one_list_core_team_member,
    ]

    return create_test_user(permission_codenames=permission_codenames, dit_team=None)
