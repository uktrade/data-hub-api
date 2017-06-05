from datahub.investment import serializers


def test_audit_log_diff_algo():
    """Test simple diff algorithm."""
    given = {
        'old': {
            'field1': 'val1',
            'field2': 'val2',
            'field3': None,
        },
        'new': {
            'field1': 'val1',
            'field2': 'new-val',
            'field3': 'added',
        },
    }

    expected = {
        'field2': ['val2', 'new-val'],
        'field3': [None, 'added'],
    }

    assert serializers.IProjectAuditSerializer._diff_versions(given['old'], given['new']) == expected
