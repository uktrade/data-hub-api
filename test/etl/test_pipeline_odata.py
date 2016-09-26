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

from etl.target_models import models
from korben import etl
from korben.sync import scrape

TEST_MAPPINGS = {
    'Categories': {
        'to': 'categories',
        'local': (
            ('ID', 'id'),
            ('Name', 'name'),
        )
    },
    'Suppliers': {
        'to': 'suppliers',
        'local': (
            ('Address_Street', 'address_street'),
            ('Address_City', 'address_city'),
            ('Address_State', 'address_state'),
            ('Address_ZipCode', 'address_zipcode'),
            ('Address_Country', 'address_country'),
            ('Concurrency', 'concurrency'),
        ),
    },
    'Products': {
        'to': 'products',
        'local': (
            ('ID', 'id'),
            ('ReleaseDate', 'release_date'),
            ('Rating', 'rating'),
            ('Price', 'price'),
            ('Name', 'name'),
            ('Description', 'description'),
            ('ReleaseDate', 'release_date'),
            ('DiscontinuedDate', 'discontinued_date'),
            ('Rating', 'rating'),
            ('Price', 'price'),
            (
                'Products_Category_Categories_ID',
                'products_category_categories_id',
            ),
            (
                'Products_Supplier_Suppliers_ID',
                'products_supplier_suppliers_id',
            ),
        ),
    },
}


def test_pipeline(odata_test_service, tmpfile, db_connection):
    etl.spec.MAPPINGS = TEST_MAPPINGS
    try:
        scrape.main(None, odata_test_service)
    except SystemExit:
        pass  # don’t ask
