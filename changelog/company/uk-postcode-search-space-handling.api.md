`POST /v4/search/company`: The behaviour of the `uk_postcode` filter was modified so that spaces are ignored only if a full postcode is searched for.

This means that `AB11` and `AB1 1` are now distinct searches (where the former would match e.g. `AB11 1AA` and the latter would match e.g. `AB1 1AA`). (Previously, both searches were equivalent and matched both postcodes.)
