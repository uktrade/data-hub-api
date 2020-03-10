import pytest
from django.urls import reverse

from datahub.company.test.factories import CompanyExportCountryHistoryFactory
from datahub.dataset.core.test import BaseDatasetViewTest


@pytest.mark.django_db
class TestCompanyExportCountryHistoryDatasetView(BaseDatasetViewTest):
    """
    Tests for CompanyExportCountryHistoryDatasetView
    """

    factory = CompanyExportCountryHistoryFactory
    view_url = reverse('api-v4:dataset:company-export-country-history-dataset')
