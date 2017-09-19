from datahub.core.utils import StrEnum


class TestScope(StrEnum):
    """Scopes used for testing and test-specific views."""

    test_scope_1 = 'test-scope-1'
    test_scope_2 = 'test-scope-2'


TEST_SCOPES_DESC = {
    TestScope.test_scope_1.value: 'Scope for testing 1.',
    TestScope.test_scope_2.value: 'Scope for testing 2.',
}
