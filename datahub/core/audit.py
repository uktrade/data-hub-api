from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.db import models
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import (
    BasePagination,
    LimitOffsetPagination,
)
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet
from reversion.models import Version

from datahub.core.audit_utils import diff_versions

User = get_user_model()


class AuditLog:
    """Class to handle audit log operations."""

    @staticmethod
    def get_version_pairs(versions: list[Version]) -> list[tuple[Version, Version]]:
        """Get pairs of consecutive versions to compare changes."""
        return [(versions[n], versions[n + 1]) for n in range(len(versions) - 1)]

    @staticmethod
    def _get_user_representation(user: Optional[User]) -> Optional[dict[str, str]]:
        """Get a dictionary representation of a user."""
        if not user:
            return None

        return {
            'id': str(user.pk),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'name': user.name,
            'email': user.email,
        }

    @classmethod
    def construct_changelog(
        cls,
        version_pairs: list[tuple[Version, Version]],
        get_additional_info: Optional[callable] = None,
    ) -> list[dict[str, Any]]:
        """Construct a changelog from version pairs."""
        changelog = []

        for v_new, v_old in version_pairs:
            version_creator = v_new.revision.user
            model_meta_data = v_new.content_type.model_class()._meta

            change_entry = {
                'id': v_new.id,
                'user': cls._get_user_representation(version_creator),
                'timestamp': v_new.revision.date_created,
                'comment': v_new.revision.get_comment() or '',
                'changes': diff_versions(
                    model_meta_data,
                    v_old.field_dict,
                    v_new.field_dict,
                ),
            }

            if get_additional_info:
                change_entry.update(get_additional_info(v_new))

            changelog.append(change_entry)

        return changelog

    @classmethod
    def get_audit_log(
        cls,
        instance: models.Model,
        paginator: Optional[BasePagination] = None,
        request: Optional[Request] = None,
        get_additional_info: Optional[callable] = None,
    ):
        """Get audit log for an instance.

        Args:
            instance: The model instance to get audit log for
            paginator: Optional paginator for instance
            request: Optional request object (needed for pagination)
            get_additional_info: Optional callback to get additional version info

        Returns:
            List of audit log entries, optionally paginated

        """
        versions = Version.objects.get_for_object(instance)
        proxied_versions = VersionQuerySetProxy(versions)

        if paginator and request:
            versions_subset = paginator.paginate_queryset(proxied_versions, request)
            version_pairs = cls.get_version_pairs(versions_subset)
            results = cls.construct_changelog(version_pairs, get_additional_info)
            return paginator.get_paginated_response(results)

        version_pairs = cls.get_version_pairs(versions)
        return cls.construct_changelog(version_pairs)


class VersionQuerySetProxy:
    """Proxies a VersionQuerySet, modifying slicing behaviour to return an extra item.

    This is allows N+1 versions to produce N audit log entires.
    """

    def __init__(self, queryset):
        """Initialises the instance, saving a reference to the underlying query set."""
        self.queryset = queryset

    def __getitem__(self, item):
        """Handles self[item], forwarding calls to underlying query set.

        Where item is a slice, 1 is added to item.stop.
        """
        if isinstance(item, slice):
            if item.step is not None:
                raise TypeError('Slicing with step not supported')

            stop = item.stop + 1 if item.stop is not None else None
            return self.queryset[item.start : stop]

        return self.queryset[item]

    def count(self):
        """Gets the count of the query set, minus 1. This is due to N audit log entries
        being generated from N+1 query set results.

        The return value is always non-negative.
        """
        return max(self.queryset.count() - 1, 0)


class AuditLogField(serializers.Field):
    """A custom field that shows the audit log for a model instance.

    Example usage:
        class MyModelSerializer(serializers.ModelSerializer):
            audit_log = AuditLogField()

        class Meta:
            model = MyModel
            fields = ['audit_log']
    """

    def __init__(self, **kwargs):
        kwargs['read_only'] = True
        super().__init__(**kwargs)

    def to_representation(self, instance):
        """Convert the instance to an audit log representation."""
        return AuditLog.get_audit_log(instance)

    def to_internal_value(self, data):
        """Convert incoming data to model field values.

        Not implemented as field is read-only.
        """
        raise NotImplementedError('AuditLogField is read-only')

    def get_attribute(self, instance):
        """Override the get_attribute method to return the instance itself.

        By default, this method maps serializer fields to attributes of the model instance;
        the result of which is passed into the to_representation method.

        Instead, we want to return the instance to pass into the AuditLog class method.
        """
        return instance


class AuditViewSet(ViewSet):
    """Generic view set for audit logs.

    Subclasses must set the queryset class attribute.

    Only the LimitOffsetPagination paginator is supported, and so this is set explicitly.
    """

    queryset = None
    pagination_class = LimitOffsetPagination

    def get_object(self):
        """Get the model object referenced in the URL path."""
        obj = get_object_or_404(self.queryset, pk=self.kwargs['pk'])
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        """Lists audit log entries (paginated)."""
        instance = self.get_object()
        return AuditLog.get_audit_log(
            instance=instance,
            paginator=self.pagination_class(),
            request=self.request,
            get_additional_info=self._get_additional_change_information,
        )

    @classmethod
    def _get_additional_change_information(cls, v_new):
        """Gets additional information about a change for the a change log entry."""
        return {}
