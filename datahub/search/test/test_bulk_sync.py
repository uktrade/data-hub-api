from unittest.mock import patch, Mock

import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import MockQuerySet
from datahub.search.bulk_sync import sync_dataset
from datahub.search.company.models import Company as ESCompany

pytestmark = pytest.mark.django_db


@patch('datahub.search.bulk_sync.bulk')
def test_sync_dataset(bulk):
    """Tests syncing a data set to Elasticsearch."""
    data_set = Mock(
        queryset=MockQuerySet([CompanyFactory(), CompanyFactory()]),
        es_model=ESCompany,
    )
    sync_dataset(data_set, batch_size=1)

    assert bulk.call_count == 2
