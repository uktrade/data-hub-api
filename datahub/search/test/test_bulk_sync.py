from unittest.mock import Mock, patch

import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import MockQuerySet
from datahub.search.bulk_sync import sync_app
from datahub.search.company.models import Company as ESCompany

pytestmark = pytest.mark.django_db


@patch('datahub.search.bulk_sync.bulk')
def test_sync_app_with_default_batch_size(bulk):
    """Tests syncing a data set to Elasticsearch."""
    data_set = Mock(
        queryset=MockQuerySet([CompanyFactory(), CompanyFactory()]),
        es_model=ESCompany,
        bulk_batch_size=100,
    )
    sync_app(data_set)

    assert bulk.call_count == 1


@patch('datahub.search.bulk_sync.bulk')
def test_sync_app_with_overridden_batch_size(bulk):
    """Tests syncing a data set to Elasticsearch."""
    data_set = Mock(
        queryset=MockQuerySet([CompanyFactory(), CompanyFactory()]),
        es_model=ESCompany,
    )
    sync_app(data_set, batch_size=1)

    assert bulk.call_count == 2
