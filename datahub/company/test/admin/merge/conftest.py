import pytest

from datahub.company.admin.merge.constants import MERGE_COMPANY_TOOL_FEATURE_FLAG
from datahub.feature_flag.test.factories import FeatureFlagFactory


@pytest.fixture()
def merge_list_feature_flag():
    """Creates the merge tool feature flag."""
    yield FeatureFlagFactory(code=MERGE_COMPANY_TOOL_FEATURE_FLAG)
