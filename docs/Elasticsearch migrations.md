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

A migration is triggered by running `./manage.py migrate_es`. (At the moment, this 
is _not_ automatically triggered during deployments.)

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

This should be rare, but if a field needs to be renamed or moved (for example, moved 
from a top-level field to a multi-field), and the field was used as part of a filter 
or was a global search field, then there are a couple more steps to do to make sure 
search continues to work during the migration:

- If the field was used in a filter, use a composite filter (using the 
`COMPOSITE_FILTERS` attribute on the view) that looks at both the old and new fields.
- If the field was used in global search, put both the old and new fields in the
search fields for the model (the `SEARCH_FIELDS` attribute on the Elasticsearch model).
- Add the old field to `PREVIOUS_MAPPING_FIELDS` on the model (otherwise tests will 
fail as it will think it’s a non-existent field).

Once the migration has been completed, you can remove references to the old field name 
from those attributes (and return composite filters to normal filters if applicable).

## Force-updating an existing mapping

If you’ve only added a field to a mapping, a full migration is technically not 
required and the existing mapping can be updated in place. (There is no automated
detection of this in the `migrate_es` command, as it’s not easy to automatically 
detect for various reasons.)

To do this, run `./manage.py init_es --model=<model name> --force-update-mapping`
followed by `./manage.py sync_es --model=<model name>`.
