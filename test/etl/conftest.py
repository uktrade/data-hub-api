import os
import tempfile

from lxml import etree
import pytest
import requests

from korben import config
from korben.cdms_api.rest.api import CDMSRestApi
from korben.cdms_api.rest.auth.noop import NoopAuth

ATOM_PREFIX = '{http://www.w3.org/XML/1998/namespace}'
ODATA_URL = 'http://services.odata.org/V2/(S(readwrite))/OData/OData.svc/'


@pytest.fixture
def tmpfile(request):
    def create():
        tmp = tempfile.NamedTemporaryFile(delete=False)
        def delete():
            os.remove(tmp.name)
        request.addfinalizer(delete)
        return tmp
    return create


@pytest.fixture
def odata_test_service(request):
    resp = requests.get(ODATA_URL)
    root = etree.fromstring(resp.content)
    config.cdms_base_url = root.attrib[ATOM_PREFIX + 'base']
    client = CDMSRestApi(NoopAuth())
    return client
