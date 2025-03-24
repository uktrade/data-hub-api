from unittest.mock import MagicMock, Mock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from rest_framework import serializers
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from datahub.core.audit import (
    AuditLog,
    AuditLogField,
    AuditViewSet,
)
from datahub.core.test.support.models import EmptyModel
from datahub.core.test_utils import MockQuerySet


class _VersionQuerySetStub(MockQuerySet):
    """VersionQuerySet stub."""

    def __init__(self, count):
        """Initialises the instance, creating some stub version instances to return as results."""
        items = [MagicMock(id=n, field_dict={}) for n in range(count)]
        super().__init__(items)


class EmptyModelSerializer(serializers.ModelSerializer):
    """Test serializer with audit log field."""

    audit_log = AuditLogField()

    class Meta:
        model = EmptyModel
        fields = ['id', 'audit_log']


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


class TestAuditLog:
    """Test suite for AuditLog class."""

    def test_get_version_pairs_with_empty_list(self):
        versions = []
        pairs = AuditLog.get_version_pairs(versions)
        assert pairs == []

    def test_get_version_pairs_with_single_version(self):
        versions = [{'id': 0}]
        pairs = AuditLog.get_version_pairs(versions)
        assert pairs == []

    def test_get_version_pairs_with_multiple_versions(self):
        versions = [{'id': 0}, {'id': 1}, {'id': 2}]
        pairs = AuditLog.get_version_pairs(versions)
        assert len(pairs) == 2
        assert pairs[0][0]['id'] == 0
        assert pairs[0][1]['id'] == 1
        assert pairs[1][0]['id'] == 1
        assert pairs[1][1]['id'] == 2

    def test_get_user_representation_with_no_user(self):
        result = AuditLog._get_user_representation(None)
        assert result is None

    def test_get_user_representation_with_valid_user(self):
        user = Mock(
            pk=0,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
        )
        user.name = 'John Doe'  # cannot set name in Mock init as it's a defined argument
        result = AuditLog._get_user_representation(user)
        assert result == {
            'id': '0',
            'first_name': 'John',
            'last_name': 'Doe',
            'name': 'John Doe',
            'email': 'john@example.com',
        }

    def test_construct_changelog_with_empty_pairs(self):
        pairs = []
        changelog = AuditLog.construct_changelog(pairs)
        assert changelog == []

    def test_construct_changelog_with_pairs(self):
        v_old = Mock()
        v_old.field_dict = {'name': 'old'}

        v_new = Mock()
        v_new.id = 1
        v_new.field_dict = {'name': 'new'}
        v_new.revision.user = Mock(
            pk=0,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
        )
        # cannot set name in Mock init as it's a defined argument
        v_new.revision.user.name = 'John Doe'
        v_new.revision.date_created = '2025-02-17'
        v_new.revision.get_comment.return_value = 'Test change'
        v_new.content_type.model_class.return_value = EmptyModel

        pairs = [(v_new, v_old)]
        changelog = AuditLog.construct_changelog(pairs)

        assert len(changelog) == 1
        entry = changelog[0]
        assert entry['id'] == 1
        assert entry['comment'] == 'Test change'
        assert entry['timestamp'] == '2025-02-17'
        assert entry['user']['name'] == 'John Doe'

    def test_construct_changelog_with_additional_info(self):
        v_old = Mock()
        v_old.field_dict = {}

        v_new = Mock()
        v_new.id = 1
        v_new.field_dict = {}
        v_new.revision.user = None
        v_new.revision.date_created = '2025-02-17'
        v_new.revision.get_comment.return_value = ''
        v_new.content_type.model_class.return_value = EmptyModel

        def get_additional_info(version):
            return {'extra': f'info-{version.id}'}

        pairs = [(v_new, v_old)]
        changelog = AuditLog.construct_changelog(pairs, get_additional_info)

        assert len(changelog) == 1
        assert changelog[0]['extra'] == 'info-1'

    @pytest.mark.parametrize(
        ('num_versions', 'expected_entries'),
        [
            (0, []),  # No versions
            (1, []),  # Single version (no changes)
            (2, [{'id': 0}]),  # Two versions (one change)
            (3, [{'id': 0}, {'id': 1}]),  # Three versions (two changes)
        ],
    )
    def test_get_audit_log(self, num_versions, expected_entries):
        with patch(
            'reversion.models.Version.objects.get_for_object',
            _create_get_for_object_stub(num_versions),
        ):
            instance = EmptyModel()
            result = AuditLog.get_audit_log(instance)

        assert len(result) == len(expected_entries)
        if expected_entries:
            for actual, expected in zip(result, expected_entries, strict=False):
                assert actual['id'] == expected['id']

    def test_get_audit_log_with_pagination(self):
        with patch(
            'reversion.models.Version.objects.get_for_object',
            _create_get_for_object_stub(10),
        ):
            instance = EmptyModel()
            paginator = LimitOffsetPagination()
            request = Mock(
                build_absolute_uri=lambda: 'http://test/audit',
                query_params={'limit': '2', 'offset': '4'},
            )

            response = AuditLog.get_audit_log(
                instance=instance,
                paginator=paginator,
                request=request,
            )

        assert response.data['count'] == 9  # 10 versions = 9 changes
        assert len(response.data['results']) == 2  # limited to 2 results
        assert _create_canonical_url_object(response.data['next']) == \
            _create_canonical_url_object('http://test/audit?limit=2&offset=6')
        assert _create_canonical_url_object(response.data['previous']) == \
            _create_canonical_url_object('http://test/audit?limit=2&offset=2')


class TestAuditField:
    """Test suite for AuditLogField, focusing on serializer-specific behaviour."""

    def test_field_is_read_only(self):
        field = AuditLogField()
        assert field.read_only is True

        with pytest.raises(NotImplementedError):
            field.to_internal_value(data={})

    def test_get_attribute_returns_instance(self):
        instance = EmptyModel()
        field = AuditLogField()
        result = field.get_attribute(instance)
        assert result is instance

    def test_integration_with_model_serialiser(self):
        with (
            patch(
                'reversion.models.Version.objects.get_for_object',
                _create_get_for_object_stub(3),
            ),
        ):
            instance = EmptyModel()
            serializer = EmptyModelSerializer(instance)

            assert 'audit_log' in serializer.data
            assert isinstance(serializer.data['audit_log'], list)
            assert len(serializer.data['audit_log']) == 2  # 3 versions = 2 changes


class TestAuditViewSet:
    """Test suite for AuditViewSet, focusing on viewset-specific behaviour."""

    def test_list_uses_pagination(self):
        with patch(
            'reversion.models.Version.objects.get_for_object',
            _create_get_for_object_stub(5),
        ):
            instance = EmptyModel()
            request = Request(APIRequestFactory().get('/', {'limit': 2, 'offset': 0}))
            viewset = AuditViewSet(request=request)

            with patch('datahub.core.audit.AuditViewSet.get_object', return_value=instance):
                response = viewset.list(request)

        assert response.data['count'] == 4  # 5 versions = 4 changes
        assert len(response.data['results']) == 2  # limited to 2 results
