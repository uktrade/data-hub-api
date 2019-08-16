from unittest.mock import Mock

import pytest

from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.notification import notify_gateway
from datahub.omis.notification.client import notify
from datahub.omis.notification.constants import OMIS_USE_NOTIFICATION_APP_FEATURE_FLAG_NAME


@pytest.fixture(params=(True, False))
def notify_client(request):
    """
    Get a reference to the correct notify client, depending on whether the
    feature flag for using the notification app is active or not.

    By using the pytest.fixture params kwarg, we ensure that every test case
    using this fixture is run once with the feature flag active (using the
    notification app) and once with the feature flag inactive (using omis' notify
    client).
    """
    use_notification_app = request.param
    if use_notification_app:
        FeatureFlagFactory(code=OMIS_USE_NOTIFICATION_APP_FEATURE_FLAG_NAME)
        client = notify_gateway.clients['omis']
    else:
        client = notify.client
    if isinstance(client, Mock):
        client.reset_mock()
    return client
