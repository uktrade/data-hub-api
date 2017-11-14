import pytest
from rest_framework import status
from rest_framework.reverse import reverse

import datahub

pytestmark = pytest.mark.django_db


def test_all_good(client):
    """Test all good."""
    url = reverse('ping')
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert '<status>OK</status>' in str(response.content)
    assert response._headers['content-type'] == ('Content-Type', 'text/xml')


@pytest.mark.parametrize('version', (None, 'fake_version'))
def test_version(client, monkeypatch, version):
    """Test the version endpoint."""
    monkeypatch.setattr(datahub, '__version__', version)

    url = reverse('api-v3:status:version')
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'version': version
    }
