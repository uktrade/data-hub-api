``GET /v4/large-investor-profile`` returns a list of all the large capital profiles.

``POST /v4/large-investor-profile`` creates a large capital profile for a given ``investor_company``.

``GET /v4/large-investor-profile/<uuid:pk>`` returns the large capital profile for the given id.

``PATCH /v4/large-investor-profile/<uuid:pk>`` updates the large capital profile for the given id.

A large capital profile consists of the following fields:
    ``id`` the uuid of the of the investor profile (readonly),


    ``investor_company`` a company (uuid and name),


    ``investor_type`` the capital investment investor type (uuid and name),


    ``investable_capital`` the capital that could be invested in USD (int),


    ``global_assets_under_management`` Global assets under management amount in USD (int),


    ``investor_description`` a text description of the investor,


    ``required_checks_conducted`` a required background checks conducted status (uuid and name),


    ``deal_ticket_sizes`` a list of deal ticket sizes (uuid and name),


    ``investment_types`` a list of large capital investment types (uuid and name),


    ``minimum_return_rate`` a return rate (uuid and name),


    ``time_horizons`` a list of time horizons (uuid and name),


    ``construction_risks`` a list of construction risks (uuid and name),


    ``minimum_equity_percentage`` an equity percentage (uuid and name),


    ``desired_deal_roles`` a list of desired deal roles (uuid and name),


    ``restrictions`` a list of restrictions (uuid and name),


    ``asset_classes_of_interest`` a list of asset class interests (uuid and name),


    ``uk_region_locations`` a list of uk regions (uuid and name),


    ``notes_on_locations`` a text field,


    ``other_countries_being_considered`` a list of countries (uuid and name),


    ``created_on`` the time and date the profile was created,


    ``modified_on`` the time and date the profile was last modified,


    ``incomplete_details_fields`` a list of the detail fields that are yet to have a value set.


    ``incomplete_requirements_fields`` a list of the requirements fields that are yet to have a value set.


    ``incomplete_location_fields`` a list of the location fields that are yet to have a value set.


The detail fields:
    ``investor_type``


    ``investable_capital``,


    ``global_assets_under_management``,


    ``investor_description``,


    ``background_checks_conducted``


The requirement fields:
    ``deal_ticket_sizes``,


    ``investment_types``,


    ``minimum_return_rate``,


    ``time_horizons``,


    ``construction_risks``,


    ``minimum_equity_percentage``,


    ``desired_deal_roles``,


    ``restrictions``,


    ``asset_classes_of_interest``


The location fields:
    ``uk_region_locations``,


    ``notes_on_locations``,


    ``other_countries_being_considered``
