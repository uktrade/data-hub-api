Extra search fields have been added to each of the search entities.

When searching, for example via `/v3/search?term=<term>`, the term will now match on the following fields:

**Companies**

- sector.name
- address.line_1.trigram
- address.line_2.trigram
- address.town.trigram
- address.county.trigram
- registered_address.line_1.trigram
- registered_address.line_2.trigram
- registered_address.town.trigram
- registered_address.county.trigram
