import pytest


@pytest.fixture
def public_omis_api_client(hawk_api_client):
    """Hawk API client fixture configured to use credentials with the OMIS scope."""
    hawk_api_client.set_credentials(
        'omis-public-id',
        'omis-public-key',
    )
    yield hawk_api_client
