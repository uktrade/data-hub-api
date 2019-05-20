``PATCH /v4/company/<uuid:pk>``: ``headquarter_type`` and ``global_headquarters`` can now always be changed. They were previously read-only if a company had a non-empty ``duns_number`` set.
