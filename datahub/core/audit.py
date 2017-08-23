from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet
from reversion.models import Version


class _VersionQuerySetProxy:
    """
    Proxies a VersionQuerySet, modifying slicing behaviour to return an extra item.

    This is allow the AuditSerializer to use the LimitOffsetPagination class
    as N+1 versions are required to produce N audit log entries.
    """

    def __init__(self, queryset):
        """Initialises the instance, saving a reference to the underlying query set."""
        self.queryset = queryset

    def __getitem__(self, item):
        """Handles instance[item], forwards calls to underlying query set.

        Where item is a slice, 1 is added to item.stop.
        """
        if isinstance(item, slice):
            if item.step is not None:
                raise TypeError('Slicing with step not supported')

            stop = item.stop + 1 if item.stop is not None else None
            return self.queryset[item.start:stop]

        return self.queryset[item]

    def count(self):
        """
        Gets the count of the query set, minus 1. This is due to N audit log entries
        being generated from N+1 query set results.

        The return value is always non-negative.
        """
        return max(self.queryset.count() - 1, 0)


class AuditViewSet(GenericViewSet):
    """Generic view set for audit logs.

    Subclasses must set the queryset class attribute.

    Only the LimitOffsetPagination paginator is supported, and so this is set explicitly.
    """

    queryset = None
    pagination_class = LimitOffsetPagination

    def list(self, request, *args, **kwargs):
        """Lists audit log entries (paginated)."""
        instance = self.get_object()
        return self.create_response(instance)

    def create_response(self, instance):
        """Creates an audit log response."""
        versions = Version.objects.get_for_object(instance)
        proxied_versions = _VersionQuerySetProxy(versions)
        versions_subset = self.paginator.paginate_queryset(proxied_versions, self.request)

        version_pairs = (
            (versions_subset[n], versions_subset[n + 1]) for n in range(len(versions_subset) - 1)
        )
        results = self._construct_changelog(version_pairs)
        return self.paginator.get_paginated_response(results)

    @classmethod
    def _construct_changelog(cls, version_pairs):
        changelog = []
        for v_new, v_old in version_pairs:
            version_creator = v_new.revision.user
            creator_repr = None
            if version_creator:
                creator_repr = {
                    'id': str(version_creator.pk),
                    'first_name': version_creator.first_name,
                    'last_name': version_creator.last_name,
                    'name': version_creator.name,
                    'email': version_creator.email,
                }

            changelog.append({
                'id': v_new.id,
                'user': creator_repr,
                'timestamp': v_new.revision.date_created,
                'comment': v_new.revision.comment or '',
                'changes': cls._diff_versions(
                    v_old.field_dict, v_new.field_dict
                ),
            })

        return changelog

    @staticmethod
    def _diff_versions(old_version, new_version):
        changes = {}

        for field_name, new_value in new_version.items():
            if field_name not in old_version:
                changes[field_name] = [None, new_value]
            else:
                old_value = old_version[field_name]
                if old_value != new_value:
                    changes[field_name] = [old_value, new_value]

        return changes
