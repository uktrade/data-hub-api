from unittest.mock import MagicMock, Mock
from urllib.parse import parse_qs, urlparse

import pytest
from reversion.models import Version

from datahub.core.audit import AuditViewSet
from datahub.core.test_utils import MockQuerySet


def test_audit_log_diff_algo():
    """Test simple diff algorithm."""
    given = {
        'old': {
            'field1': 'val1',
            'field2': 'val2',
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

    assert AuditViewSet._diff_versions(given['old'], given['new']) == expected


@pytest.mark.parametrize(
    'num_versions,offset,limit,exp_results,exp_next,exp_previous',
    (
        (0, '', '', [], None, None),
        (1, '', '', [], None, None),
        (2, '', '', [0], None, None),
        (26, '', '', range(0, 25), None, None),
        (
            26, '10', '10', range(10, 20), 'http://test/audit?offset=20&limit=10',
            'http://test/audit?limit=10',
        ),
        (26, '20', '10', range(20, 25), None, 'http://test/audit?offset=10&limit=10'),
    ),
)
def test_audit_log_pagination(
    num_versions, offset, limit, exp_results, exp_next, exp_previous,
    monkeypatch,
):
    """Test the audit log pagination."""
    monkeypatch.setattr(
        Version.objects, 'get_for_object', _create_get_for_object_stub(num_versions),
    )
    instance = Mock()
    request = Mock(
        build_absolute_uri=lambda: 'http://test/audit',
        query_params={
            'offset': offset,
            'limit': limit,
        },
    )
    serializer = AuditViewSet(request=request)
    response = serializer.create_response(instance)
    results = response.data['results']

    assert response.data['count'] == max(num_versions - 1, 0)
    assert _create_canonical_url_object(response.data['next']) == _create_canonical_url_object(
        exp_next,
    )
    assert _create_canonical_url_object(response.data['previous']) == _create_canonical_url_object(
        exp_previous,
    )
    assert [result['id'] for result in results] == list(exp_results)


class _VersionQuerySetStub(MockQuerySet):
    """VersionQuerySet stub."""

    def __init__(self, count):
        """Initialises the instance, creating some stub version instances to return as results."""
        items = [MagicMock(id=n) for n in range(count)]
        super().__init__(items)


def _create_get_for_object_stub(num_versions):
    """Creates a stub replacement for Version.objects.get_for_object."""
    def mock_versions(obj, model_db=None):
        return _VersionQuerySetStub(num_versions)

    return mock_versions


def _create_canonical_url_object(url):
    """Turns a URL into an object in a canonical form that can be used for comparisons."""
    if url is None:
        return None
    parse_results = urlparse(url)
    parsed_dict = parse_results._asdict()
    parsed_dict['query'] = parse_qs(parse_results.query)
    return parsed_dict
