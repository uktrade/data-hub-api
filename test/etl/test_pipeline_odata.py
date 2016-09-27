'''
Test the ETL pipeline and polling sync against an OData test service. It runs
in a slightly simpler container environment (since custom Postgres compilation
isn’t required here). It basically does this:
    - Overwrite transformation mapping (since this test doesn’t run against the
      full CDMS schema)
    - Make changes in the OData service through the API (ie. simulate updates)
    - Check these updates are caught by the polling sync and that an ETL run is
      triggered
    - Test should cases cover verfication that “intermediate” and “production”
      databases are in the expected state
'''

from korben import etl
from korben.sync import scrape, django_initial

def test_initial_etl(tier0, odata_test_service, odata_fetchall):

    # due to django's high level of awesomeness, we must import models here
    # (ie. after tier0 fixture has initiated full django awesomeness levels)
    from etl.target_models import models as target_models

    # call scrape code on test service
    scrape.main(None, odata_test_service)  # uses multiprocessing, but will
                                           # block until CHUNKSIZE pages are
                                           # processed
    expected = (
        (2, 'Suppliers'),
        (9, 'Products'),
        (3, 'Categories'),
    )
    for count, table_name in expected:
        result = odata_fetchall(
            'SELECT count(*) FROM "{0}"'.format(table_name)
        )
        assert count == result[0][0]

    # call django initial load function to move data through the ETL
    django_initial.main(odata_test_service)
    for count, model_name in expected:
        assert count == getattr(target_models, model_name).objects.count()
