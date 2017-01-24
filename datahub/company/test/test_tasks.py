import datetime
from unittest import mock

import pytest
from celery.exceptions import Retry
from django.utils.timezone import now

from datahub.company.tasks import save_to_korben
from datahub.core.models import TaskInfo
from datahub.core.test_utils import get_test_user

# mark the whole module for db use
from datahub.korben.exceptions import KorbenException

pytestmark = pytest.mark.django_db


@mock.patch('datahub.company.tasks.KorbenConnector')
def test_save_to_korben_task_stale_object(mocked_korben_connector):
    """Save to Korben task works."""
    date_in_the_future = datetime.datetime.now() + datetime.timedelta(1)
    mocked_korben_connector().get.return_value.json.return_value = {
        'modified_on': date_in_the_future.isoformat()
    }
    user = get_test_user()

    save_to_korben(
        data={'modified_on': now().isoformat()},
        user_id=str(user.id),
        db_table='company_company',
        update=True
    )

    # check save_to_korben called
    assert mocked_korben_connector().post.called is False


@mock.patch('datahub.company.tasks.KorbenConnector')
def test_save_to_korben_update_happy_path(mocked_korben_connector):
    """Save to Korben task works."""
    date_in_the_past = datetime.datetime.now() + datetime.timedelta(-1)
    mocked_korben_connector().get.return_value.json.return_value = {
        'modified_on': date_in_the_past.isoformat()
    }
    user = get_test_user()

    save_to_korben(
        data={'foo': 'bar', 'modified_on': now().isoformat()},
        user_id=str(user.id),
        db_table='company_company',
        update=True
    )

    # check save_to_korben called
    assert mocked_korben_connector().post.called


@mock.patch('datahub.company.tasks.KorbenConnector')
def test_save_to_korben_create_happy_path(mocked_korben_connector):
    """Save to Korben task works."""
    mocked_korben_connector().get.return_value.json.return_value = {}
    user = get_test_user()

    save_to_korben(
        data={'foo': 'bar', 'modified_on': now().isoformat()},
        user_id=str(user.id),
        db_table='company_company',
        update=True
    )

    # check save_to_korben called
    assert mocked_korben_connector().post.called


@mock.patch('datahub.company.tasks.KorbenConnector')
@mock.patch('datahub.company.tasks.client')
@mock.patch('datahub.company.tasks.save_to_korben.retry', mock.Mock(side_effect=Retry))
def test_save_to_korben_retry_exception(mocked_sentry_client, mocked_korben_connector):
    """Save to Korben task works."""
    mocked_korben_connector().post.side_effect = KorbenException()
    date_in_the_past = datetime.datetime.now() + datetime.timedelta(-1)
    mocked_korben_connector().get.return_value.json.return_value = {
        'modified_on': date_in_the_past.isoformat()
    }
    user = get_test_user()

    with pytest.raises(Retry):
        save_to_korben(
            data={'foo': 'bar', 'modified_on': now().isoformat()},
            user_id=str(user.id),
            db_table='company_company',
            update=True
        )
        mocked_sentry_client.captureException.assert_called_once_with()
