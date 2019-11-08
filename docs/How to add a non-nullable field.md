# How to add a non-nullable field to a large table

## Overview

When tables are large in PostgreSQL, adding a text field which is not null can be 
problematic. Setting a DB-enforced default value will cause Postgres to set the default value for 
every existing row in the table.  Since our migrations
run in a transaction, the table in question will become locked during the 
migration which could cause the application to grind to a halt. This is problematic 
if there could be writes happening to the table during deployment.
Adding a (nullable or non-nullable) column with a default can be problematic for 
large tables because the ALTER TABLE statement will cause a full table rewrite 
(for PostgreSQL < 11) during which time the table will be locked (pretty much completely...).

## A Multi-step Approach

Instead of adding a non-nullable field with a single DB migration, we must take
a multiple-step approach.  These steps should be merged and released separately:

1) Add the new DB field as a nullable field in a django migration.  Ensure that
   any code which can add new entries (e.g. API views) adds them with a 
   default value for this field.
2) Manually run our `datahub.dbmaintenance.tasks.replace_null_with_default` task
   for the field in question.  e.g. `replace_null_with_default.apply_async(args=("interaction", "status", "complete"))`
   This function is a recursive celery task - it will set the default value in
   small batches which ensure that the table is responsive while the default is
   added.
   **Note:** This task will need to be run in at least the dev, staging and 
   production environments.
3) Set the DB field as not nullable with a sensible default in a django migration.
   Adding a default value will ensure that any local dev environments are also 
   picked up.
   **Note:** In the case of multiple fields, there must be one migration per
   field due to: https://code.djangoproject.com/ticket/25105

## Example

This process has been carried out a number of times in the Data Hub backend
repo, here is a concrete example (including work to enforce defaults through the
API) for adding a boolean field `archived` to the `interaction` model:

Initial nullable PR:
https://github.com/uktrade/data-hub-api/pull/1627

Follow-up PR to set as not-nullable:
https://github.com/uktrade/data-hub-api/pull/1679
