from unittest import mock
from unittest.mock import Mock

import pytest
from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status
from reversion.models import Version

from datahub.company.test.factories import CompanyFactory
from datahub.core.mixins import DeferredSaveModelMixin
from datahub.core.test_utils import LeelooTestCase
from datahub.korben.exceptions import KorbenException

frozen_now = now()
model_dict = {'foo': 'hello', 'bar': str(frozen_now)}


class DummyModel(DeferredSaveModelMixin):
    """Dummy model class using DeferredSaveModelMixin."""

    foo = 'hello'
    bar = frozen_now

    def _get_table_name_from_model(self):
        return

    def _convert_model_to_korben_format(self):
        return model_dict

    def save(self, as_korben=False, **kwargs):
        """Dummy save."""
        pass


@mock.patch('datahub.core.mixins.KorbenConnector')
def test_update_from_korben_model_didnt_change(mocked_korben_connector):
    """Korben return the same object."""
    mocked_response = Mock()
    mocked_response.status_code = status.HTTP_200_OK
    mocked_response.json.return_value = model_dict
    mocked_korben_connector().get.return_value = mocked_response
    class_instance_under_test = DummyModel()
    assert class_instance_under_test.update_from_korben() == class_instance_under_test


@mock.patch('datahub.core.mixins.KorbenConnector')
def test_update_from_korben_404_scenario(mocked_korben_connector):
    """Korben 404."""
    mocked_response = Mock()
    mocked_response.status_code = status.HTTP_404_NOT_FOUND
    mocked_response.json.return_value = model_dict
    mocked_korben_connector().get.return_value = mocked_response
    class_instance_under_test = DummyModel()
    assert class_instance_under_test.update_from_korben() == class_instance_under_test


@mock.patch('datahub.core.mixins.KorbenConnector')
def test_update_from_korben_500_scenario(mocked_korben_connector):
    """Korben 500."""
    mocked_response = Mock()
    mocked_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    mocked_response.json.return_value = model_dict
    mocked_korben_connector().get.return_value = mocked_response
    class_instance_under_test = DummyModel()

    with pytest.raises(KorbenException):
        class_instance_under_test.update_from_korben()


class KorbenUpdateTestCase(LeelooTestCase):
    """Korben update test case talking to the API."""

    @mock.patch('datahub.core.mixins.KorbenConnector')
    def test_update_from_korben_different_object(self, mocked_korben_connector):
        """Korben return a different object."""
        company = CompanyFactory()
        company_dict = company._convert_model_to_korben_format()
        korben_response_dict = dict(company_dict, name='new-name')

        for name in company.get_datetime_fields():
            if korben_response_dict[name]:
                korben_response_dict[name] = korben_response_dict[name].isoformat()

        mocked_response = Mock()
        mocked_response.status_code = status.HTTP_200_OK
        mocked_response.json.return_value = korben_response_dict
        mocked_korben_connector().get.return_value = mocked_response

        url = reverse('company-detail', kwargs={'pk': company.id})
        self.api_client.get(url)
        version = Version.objects.get_for_object(company)
        assert version[0].field_dict['name'] == 'new-name'
