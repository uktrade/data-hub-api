Two metdata API endpoints were added for One List Tiers.
``GET /metadata/one-list-tier/`` and ``GET /v4/metadata/one-list-tier`` list 
all One List Tier models in the following format::

    [
        {
            "id": "b91bf800-8d53-e311-aef3-441ea13961e2",
            "name": "Tier A - Strategic Account",
            "disabled_on": null
        },
        ...,
    ]
