New API endpoints were added to aid matching Data Hub companies with D&B companies:

All endpoints return a response body with the following format::

    {
        "result": {
            ...
        },
        "candidates": [
            { ... },
            { ... }
        ],
        "company": {
            "id": "81756b9a-5d95-e211-a939-e4115bead28a",
            "name": 'My Corp',
            "trading_names": ["trading name"]
        }
    }

The value of ``result`` depends on the type of match.

If a match was found and recorded::

    {
        "dnb_match": {
            "duns_number": "111",
            'name': 'NAME OF A COMPANY',
            "country": {
                "id": "81756b9a-5d95-e211-a939-e4115bead28a",
                "name": "United States"
            },
            "global_ultimate_duns_number": "112",
            "global_ultimate_name": "NAME OF A GLOBAL COMPANY",
            "global_ultimate_country": {
                "id": "81756b9a-5d95-e211-a939-e4115bead28a",
                "name": "United States"
            },
        },
        "matched_by": "data-science"
    },

If ``matched_by`` contains ``adviser`` value, then additional ``adviser`` key will be added to the ``result`` response::

    {
        ...
        "matched_by": "adviser",
        "adviser": {
            "id": "12777b9a-5d95-2241-a939-fa112be2d22a",
            "first_name": "John",
            "last_name": "Doe",
            "name": "John Doe"
        }
    },

If a match wasn't found because the company isn't listed or the adviser is not confident to make the match::

    {
        "no_match": {
            "reason': "not_listed",  # or "not_confident"
        },
        "matched_by": "adviser",
        "adviser": { ... }
    },

If a match wasn't found because there were multiple potential matches::

    {
        "no_match": {
            "reason": "more_than_one",
            "candidates": [  # list of duns numbers
                "123456789",
                "987654321"
            ]
        },
        "matched_by": "adviser",
        "adviser": { ... }
    },

If a match wasn't found because of other reasons::

    {
        "no_match": {
            "reason": "other",
            "description": "explanation..."
        },
        "matched_by": "adviser",
        "adviser": { ... }
    },

The top level ``candidates`` is a list of objects with this format::

    {
        "duns_number": 12345,
        "name": 'test name',
        "global_ultimate_duns_number": 12345,
        "global_ultimate_name": "test name global",
        "global_ultimate_country": {
            "id": "81756b9a-5d95-e211-a939-e4115bead28a",
            "name": "United States"
        },
        "address_1": "1st LTD street",
        "address_2": "",
        "address_town": "London",
        "address_postcode": "SW1A 1AA",
        "address_country": {
            "id": "81756b9a-5d95-e211-a939-e4115bead28a",
            "name": "United States"
        },
        "confidence": 10,
        "source": "cats"
    }

Endpoints:

``GET /v4/dnb-match/<company_pk>`` returns the response above

``POST /v4/dnb-match/<company_pk>/select-match`` accepts the ``duns_number`` of the candidate to be selected as a match from the list of candidates

``POST /v4/dnb-match/<company_pk>/select-no-match`` accepts ``reason`` with value:

- ``not_listed``: if none of the candidates is a good match
- ``not_confident``: if the adviser is not confident to make the match
- ``more_than_one``: if there are multiple potential matches. In this case an extra ``candidates`` field is required with the list of valid duns numbers.
- ``other``: for other reasons. In this case an extra free text ``description`` field is required
