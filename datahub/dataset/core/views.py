from rest_framework.views import APIView

from config.settings.types import HawkScope
from datahub.core.auth import PaaSIPAuthentication
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.dataset.core.pagination import DatasetCursorPagination


class BaseDatasetView(HawkResponseSigningMixin, APIView):
    """Base API view to be used for creating endpoints for consumption
    by Data Flow and insertion into Data Workspace.
    """

    authentication_classes = (PaaSIPAuthentication, HawkAuthentication)
    permission_classes = (HawkScopePermission,)
    required_hawk_scope = HawkScope.datasets
    pagination_class = DatasetCursorPagination

    def get(self, request):
        """Endpoint which serves all records for a specific Dataset."""
        self._get_request_params(request)
        dataset = self.get_dataset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dataset, request, view=self)
        self._enrich_data(page)
        return paginator.get_paginated_response(page)

    def _get_request_params(self, request):
        """Hook for checking request parameters before querying dataset.
        By default it does nothing, but subclasses can use it to modify the query set,
        based on user parameters.
        """
        pass

    def _enrich_data(self, dataset):
        """Hook for enriching the paged dataset before returning a response.
        By default it does nothing but can be changed in subclasses to make
        calls to external APIs if required.
        """
        return dataset

    def get_dataset(self):
        """Return a list of records."""
        raise NotImplementedError


class BaseFilterDatasetView(HawkResponseSigningMixin, APIView):
    """Base API view to be used for creating endpoints for consumption
    by Data Flow and insertion into Data Workspace.
    """

    authentication_classes = (PaaSIPAuthentication, HawkAuthentication)
    permission_classes = (HawkScopePermission,)
    required_hawk_scope = HawkScope.datasets
    pagination_class = DatasetCursorPagination

    def get(self, request):
        """Endpoint which serves all records for a specific Dataset."""
        dataset = self.get_dataset(request=request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dataset, request, view=self)
        self._enrich_data(page)
        return paginator.get_paginated_response(page)

    def _enrich_data(self, dataset):
        """Hook for enriching the paged dataset before returning a response.
        By default it does nothing but can be changed in subclasses to make
        calls to external APIs if required.
        """
        return dataset

    def get_dataset(self, request=None):
        """Return a list of records."""
        raise NotImplementedError
