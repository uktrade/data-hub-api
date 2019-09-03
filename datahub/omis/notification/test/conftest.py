from unittest.mock import Mock

import pytest

from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.notification import notify_gateway
from datahub.omis.notification.client import notify
from datahub.omis.notification.constants import OMIS_USE_NOTIFICATION_APP_FEATURE_FLAG_NAME


@pytest.fixture(params=(True, False))
def use_notification_app(request):
    """
    Fixture determining whether or not to use omis' notification package or
    datahub's new datahub.notification django app.

    By using the pytest.fixture params kwarg, we ensure that every test case
    using this fixture is run once with the feature flag active (using the
    notification app) and once with the feature flag inactive (using omis' notify
    client).
    """
    use_notification_app = request.param
    if use_notification_app:
        FeatureFlagFactory(code=OMIS_USE_NOTIFICATION_APP_FEATURE_FLAG_NAME)
        return True
    return False


@pytest.fixture()
def mocked_notify_client(use_notification_app):
    """
    Get a reference to the correct mocked GOVUK notify client, depending on whether the
    feature flag for using the notification app is active or not.
    """
    if use_notification_app:
        client = notify_gateway.clients['omis']
    else:
        client = notify.client
    if not isinstance(client, Mock):
        raise Exception(
            'mocked_notify_client fixture called, but notification client is not '
            'a Mock() object.',
        )
    client.reset_mock()
    return client
