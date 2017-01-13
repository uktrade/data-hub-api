import datetime
from unittest import mock
import pytest

from celery.exceptions import Retry

from datahub.company.tasks import save_to_korben
from datahub.company.test.factories import CompanyFactory
from datahub.core.models import TaskInfo
from datahub.core.test_utils import get_test_user

# mark the whole module for db use
from datahub.korben.exceptions import KorbenException

pytestmark = pytest.mark.django_db


@mock.patch('datahub.core.mixins.DeferredSaveModelMixin.save_to_korben')
def test_save_to_korben_task_happy_path(mocked_save_to_korben):
    """Save to Korben task works."""
    company = CompanyFactory()
    user = get_test_user()

    save_to_korben(
        object_id=str(company.id),
        user_id=str(user.id),
        db_table='company_company',
        update=True
    )

    # check task info created
    assert TaskInfo.objects.get(user=user)
    # check save_to_korben called
    assert mocked_save_to_korben.called_once_with(False)


@mock.patch('datahub.core.mixins.DeferredSaveModelMixin.save_to_korben')
@mock.patch('datahub.company.tasks.KorbenConnector')
def test_save_to_korben_task_stale_object(mocked_korben_connector, mocked_save_to_korben):
    """Save to Korben task works."""
    date_in_the_future = datetime.datetime.now() + datetime.timedelta(1)
    mocked_korben_connector().get.return_value.json.return_value = {
        'modified_on': date_in_the_future.isoformat()
    }
    company = CompanyFactory()
    user = get_test_user()

    save_to_korben(
        object_id=str(company.id),
        user_id=str(user.id),
        db_table='company_company',
        update=True
    )

    task_info = TaskInfo.objects.get(user=user)
    assert task_info.note == 'Stale object, not saved.'
    # check save_to_korben called
    assert mocked_save_to_korben.called is False


@mock.patch('datahub.core.mixins.DeferredSaveModelMixin.save_to_korben')
@mock.patch('datahub.company.tasks.client')
@mock.patch('datahub.company.tasks.save_to_korben.retry', mock.Mock(side_effect=Retry))
def test_save_to_korben_retry_exception(mocked_sentry_client, mocked_save_to_korben):
    """Save to Korben task works."""
    mocked_save_to_korben.side_effect = KorbenException()
    company = CompanyFactory()
    user = get_test_user()

    with pytest.raises(Retry):
        save_to_korben(
            object_id=str(company.id),
            user_id=str(user.id),
            db_table='company_company',
            update=True
        )
        mocked_sentry_client.captureException.assert_called_once_with()
