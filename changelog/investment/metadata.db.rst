The following metadata database tables have been added:
    ``investor_profile_assetclassinterestsector``
    ``investor_profile_backgroundchecksconducted``
    ``investor_profile_constructionrisk``
    ``investor_profile_dealticketsize``
    ``investor_profile_desireddealrole``
    ``investor_profile_equitypercentage``
    ``investor_profile_investortype``
    ``investor_profile_largecapitalinvestmenttype``
    ``investor_profile_profiletype``
    ``investor_profile_relationshiphealth``
    ``investor_profile_restriction``
    ``investor_profile_returnrate``
    ``investor_profile_timehorizon``

Each table has the following columns:
    ``id (uuid) not null``,
    ``name (text) not null``,
    ``order (float) not null``.

The metadata table``investor_profile_assetclassinterest`` has the columns
    ``id (uuid) not null``,
    ``name (text) not null``,
    ``order (float) not null``,
    ``asset_class_interest_sector_id (uuid) not null``.
