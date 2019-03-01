``POST /v4/public/search/company`` was added as a Hawk-authenticated company search endpoint. This is similar to
``POST /v4/search/company`` but has a reduced set of filters (``name``, ``archived`` and ``original_query``) and
slightly reduced set of response fields.
