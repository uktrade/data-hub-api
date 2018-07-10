from unittest import mock

import pytest
from dateutil.relativedelta import relativedelta
from dateutil.utils import today
from django.apps import apps
from django.core import management
from django.utils.timezone import utc

from datahub.cleanup.management.commands import delete_orphans
from datahub.cleanup.test.commands.test_common import create_orphanable_model, MAPPINGS
from datahub.core.exceptions import DataHubException

pytestmark = pytest.mark.django_db

CONFIGS = delete_orphans.Command.CONFIGS


@mock.patch('datahub.search.deletion.bulk')
@pytest.mark.usefixtures('synchronous_on_commit')
def test_with_es_exception(mocked_bulk):
    """
    Test that if ES returns a 5xx error, the command completes but it also
    raises a DataHubException with details of the error.
    """
    mocked_bulk.return_value = (None, [{'delete': {'status': 500}}])

    model_name = next(iter(delete_orphans.Command.CONFIGS))
    model_factory = MAPPINGS[model_name]['factory']
    orphaning_config = delete_orphans.Command.CONFIGS[model_name]

    orphaning_datetime = today(tzinfo=utc) - orphaning_config.age_threshold - relativedelta(days=1)
    create_orphanable_model(model_factory, orphaning_config, orphaning_datetime)

    with pytest.raises(DataHubException):
        management.call_command(delete_orphans.Command(), model_name)

    model = apps.get_model(model_name)
    assert model.objects.count() == 0
