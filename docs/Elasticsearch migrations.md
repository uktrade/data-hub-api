# Elasticsearch mapping migrations

When certain changes to a field in the mapping for an Elasticsearch model (also 
known as a mapping or document type) are made, the mapping needs to be _migrated_.

This document describes how the migration process works (as implemented in this app).

## Indexes and aliases during normal operation

During normal operation, Elasticsearch the following indexes and aliases exist:

- There is one index per Elasticsearch model. Index 
names follow the following pattern: `<prefix>-<model name>-<mapping hash>`.
- There are two aliases per model:
  - `<prefix>-<model name>-read` (used for searches)
  - `<prefix>-<model name>-write` (used for document updates and creations)

(The prefix is defined by the `ES_INDEX_PREFIX` setting.)

The `./manage.py init_es` command creates indexes and aliases as described above.

The mapping hash is calculated by hashing the mapping as defined in the code base
(rather than the mapping as returned by the Elasticsearch server). This is because
there are subtle differences between the mapping as given to Elasticsearch and the
mapping it returns.

## Operation during a migration

A migration is triggered by running `./manage.py migrate_es`. (This 
is automatically run during deployment.)

This command:

1. Creates new indexes (in the `<prefix>-<model name>-<mapping hash>` format) using 
the new mapping hashes (where the mapping hash has changed).

2. Updates `<prefix>-<model name>-read` aliases to include the new indexes (in 
addition to the old ones).

3. Updates `<prefix>-<model name>-write` aliases to point at the new indexes 
(instead of the old ones).
  
   At this point, if an object is updated or created, the document is updated in the 
new index, and the old version of the document is deleted from the old index.

4. Celery tasks are queued to migrate data from the old indexes to the new indexes 
(one task per search app and model). This is done by indexing documents afresh 
in batches. Once each batch has been successfully created in the new index, it 
is deleted from the old index.
   
   During this period, search requests may return a small number of duplicates as 
some documents in any particular batch being migrated will exist in both the old and 
new index. Batches are typically around 1000-2000 documents in size, so the overall
impact of this should be minimal.

5. Once a model has been migrated, it is removed from the `<prefix>-<model name>-read`
   alias. If no aliases that reference the old index remain, the old index is deleted.

## Renaming and moving fields

This should be uncommon, but if a field needs to be renamed or moved (for example, moved 
from a top-level field to a multi-field), and the field was used as part of a filter 
or was a global search field, then there are a couple more steps to do to make sure 
search continues to work during the transition.

If the field is returned in search responses, is a sort-by option, or there is more 
complex logic relating to the field:

1. Add the new field, keeping the old field in place and existing query logic unchanged.
2. Add a news fragment deprecating the old field.
3. Release this, and populate the new field with data by running `./manage.py migrate_es`.
4. Update query logic (global search fields, filters, sort-by options etc.) to use the new 
field, and remove the old field once the deprecation period has expired.

In simpler cases, you can avoid the intermediate release by adding and removing the 
field at the same time (but only do this if you are sure that it is safe):

1. Simultaneously add the new field and remove the old field from the search model.
2. If the field was used in a filter, use a composite filter (using the 
`COMPOSITE_FILTERS` attribute on the view) that looks at both the old and new fields.
3. If the field was used in global search, put both the old and new fields in the
search fields for the model (the `SEARCH_FIELDS` attribute on the Elasticsearch model).

   (Note: It’s important that both fields don’t exist on the same document at the same time, 
as this will affect scores calculated during searches.)
4. Add the old field to `PREVIOUS_MAPPING_FIELDS` on the model (otherwise tests will 
fail as they will assume it’s a non-existent field).
5. Release this, and run `./manage.py migrate_es`.
6. Remove references to the old field from the attributes mentioned in previous steps 
(and return composite filters to normal filters if applicable).
