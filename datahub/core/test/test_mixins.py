from unittest import mock
from unittest.mock import Mock

from django.utils.timezone import now
from requests import Response
from rest_framework import status

from datahub.core.mixins import DeferredSaveModelMixin

frozen_now = now()


class DummyModel(DeferredSaveModelMixin):
    """Dummy model class using DeferredSaveModelMixin."""

    foo = 'hello'
    bar = frozen_now


@mock.patch('datahub.core.mixins.KorbenConnector')
def test_update_from_korben(mocked_korben_connector):
    mocked_response = Mock(status_code=status.HTTP_200_OK, spec_set=Response)
    mocked_response.json.return_value = {'foo': 'hello', 'bar': frozen_now.isoformat()}
    mocked_korben_connector.get.return_value = mocked_response
    class_under_test = DummyModel()
    assert class_under_test.update_from_korben() == class_under_test
