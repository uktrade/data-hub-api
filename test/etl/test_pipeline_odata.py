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

from etl.target_models import models as target_models

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


def test_pipeline(odata_test_service, db_odata):
    from korben import etl
    from korben.sync import scrape
    etl.spec.MAPPINGS = TEST_MAPPINGS
    scrape.main(None, odata_test_service)  # uses multiprocessing, but will
                                           # block until CHUNKSIZE pages are
                                           # processed
    expected = (
        (2, 'Suppliers'),
        (9, 'Products'),
        (3, 'Categories'),
    )
    for count, table_name in expected:
        result = db_odata('SELECT count(*) FROM "{0}"'.format(table_name))
        assert expected == result[0][0]  # <-- use a pair of spectacles
