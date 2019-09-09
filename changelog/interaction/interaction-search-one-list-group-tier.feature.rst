The ``/v3/search/interaction/`` endpoint was modified to return 
``company_one_list_group_tier`` in search results. This will be in the following
format:


```
...
"company_one_list_group_tier": {
    "id": "b91bf800-8d53-e311-aef3-441ea13961e2",
    "name": "Tier A - Strategic Account"
}
...
```

The value could alternatively be null (if the interaction's company does not
have a one list group tier).

A filter was added to ``/v3/search/interaction/`` - ``company__one_list_group_tier`` -
which allows callers to filter interaction searches to companies attributed to a
particular one list group tier.
