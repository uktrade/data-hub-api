import os
import tempfile

from lxml import etree
import pytest
import requests
import sqlalchemy as sqla

from korben import cdms_api, config
from korben.cdms_api.rest.auth.noop import NoopAuth

ATOM_PREFIX = '{http://www.w3.org/XML/1998/namespace}'
ODATA_URL = 'http://services.odata.org/V2/(S(readwrite))/OData/OData.svc/'


@pytest.fixture(scope='session')
def db_engine():
    return sqla.create_engine(config.database_odata_url).connect()


@pytest.fixture
def db_connection(db_engine):
    return db_engine.connect()


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
    client = cdms_api.rest.api.CDMSRestApi(NoopAuth())
    client.CDMS_REST_BASE_URL = root.attrib[ATOM_PREFIX + 'base']
    return client
