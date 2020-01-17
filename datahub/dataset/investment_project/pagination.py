"""
Pagination serializers determine the structure of the output that should
be used for paginated responses.
"""

from rest_framework.response import Response

from datahub.dataset.core.pagination import DatasetCursorPagination
from datahub.dataset.investment_project.spi import SPIReportFormatter


class InvestmentProjectActivityDatasetViewCursorPagination(DatasetCursorPagination):
    """Cursor Pagination for SPI Report."""

    ordering = ('created_on', 'pk')

    def get_paginated_response(self, data):
        """Get paginated response."""
        spi_report = SPIReportFormatter()
        results = spi_report.format(data)
        return Response(
            {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': results,
            },
        )
