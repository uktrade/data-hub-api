from datahub.dataset.core.pagination import DatasetCursorPagination


class HCSATDatasetViewCursorPagination(DatasetCursorPagination):
    ordering = ('created_on', 'pk')
