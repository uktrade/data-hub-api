The `format_dnb_company` now includes a check for `annual_sales_currency`.

If `annual_sales_currency` is not US Dollars, we do not propagate `annual_sales` or `is_annual_sales_estimated` fields downstream.

All D&B records that we have encountered until now have `annual_sales` in US dollars but we would like to monitor this behavior and not ingest bad data in case there is an exception.
