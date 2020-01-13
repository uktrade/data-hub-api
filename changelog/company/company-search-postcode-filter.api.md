`POST /v4/search/company`: A `uk_postcode` filter was added for the `address_postcode` and `registered_address_postcode` 
fields for UK based companies. The filter accepts a single or a partial postcode as well as an array of postcodes. 
Multiple postcodes are matched with `or` query.
