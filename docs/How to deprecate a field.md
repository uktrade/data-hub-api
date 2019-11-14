# How to deprecate, remove or rename a field

## Overview

Removing or changing an API field or a database column requires weeks so please plan ahead with your team.

We currently use blue-green deployments with zero downtime but with a single database. This means that for some time an old instance of the application could have an active connection to the most up-to-date version of the database. Please implement your changes with this architecture design in mind.

## <a name="document-deprecation"></a> Document the deprecation in the changelog

All changes need to be announced first using the changelog/release notes so that people are aware of it.

This is currently done by creating [newsfragments](../changelog/) with details of the change and ideally instructions on what to do.

To do that:

* Create an `.api `, `.deprecation` and, if necessary, a `.db` newsfragment announcing the change. See [example](https://github.com/uktrade/data-hub-api/commit/ff5484b4331cd8a42dfd962d00438274d9edc6a6).
* Open a PR and merge it into develop after it's been approved.
* Wait for the next release; your changes will appear in the release notes.

**Include a date in your newsfragment** (e.g. _this field will be removed on or after August 30_) so that people don't procrastinate.
We have weekly releases every Thursday so give at least one week of notice from the approaching release date. E.g. if today is September 12 and you are sure your PR will be merged before September 13, the earliest date to use in the changelog is September 20.

## <a name="how-to-remove-from-api"></a>How to remove a field from the API

### Remove the field from the codebase

* Make sure you announced the deprecation in a previous release.
* Remove the field from:
    * the DRF serializer
    * the search model
    * the search serializer
    * the tests
    * the fixtures (`test_data`)
    * any other place
* Check that the [frontend](https://github.com/uktrade/data-hub-frontend) doesn't have any references to it.
* Create an `.api` and `.removal` newsfragment announcing the removal.
* Open a PR and merge it into develop after it's been approved.
* Wait for the next release; your changes will appear in the release notes.

If you are removing a model field you might want to start [removing it from django](#how-to-remove-column) at the same time.

See [example](https://github.com/uktrade/data-hub-api/pull/1107/files).

### Migrate elasticsearch

If the field was included in the search, you need to migrate the ES mapping as well.

**Please ask other developers first as this is a newish process.**

Instructions on how to do this can be found in the [elasticsearch mapping migration guide](./Elasticsearch&#32;migrations.md).

## <a name="how-to-remove-column"></a>How to remove a column from the database

### Deprecate and remove from the API

If the column is used in the API, you need to [deprecate](#document-deprecation) and [remove it form the API first](#how-to-remove-from-api).

You can remove the field from the API and from django at the same time (see next section) if you have previously deprecated both.

### Remove the field from django but keep the database column

The field has to be removed from the django model while keeping the database column. This is a necessary step to allow the blue/green deployment to complete without any issues.

If the field has a NOT NULL constraint you need to create a migration to change the column to be nullable as well.

To do this:
* Make sure you announced the deprecation in a previous release.
* Make the field nullable if necessary. See [example](https://github.com/uktrade/data-hub-api/blob/d57e613aad6c4c033131f0b3074e6143bd4fb010/datahub/company/migrations/0036_update_contact_contactable_columns.py):
    * Change the django field in `models.py`.
    * Create a migration `./manage.py makemigrations <app> --name=remove_<field>_from_django`.
* Remove the field from the django model.
* Add the logic that removes the field from django while keeping the column:
    * Open the `xxxx_remove_<field>_from_django.py` file if you made the field nullable or create an empty one with `./manage.py makemigrations <app> --empty --name=remove_<field>_from_django` otherwise.
    * Add a `migrations.SeparateDatabaseAndState` operation following [this example](https://github.com/uktrade/data-hub-api/blob/d4b7d447cb992f71427ac56b219d4a63c73fbb2b/datahub/company/migrations/0034_remove-account-manager-from-django.py).
    * `./manage.py migrate`.
* Remove the field from any other part of the code including factories, admin and tests.
* Create a `.removal` and, if necessary, a `.db` newsfragment announcing the change.
* Open a PR and merge it into develop after it's been approved.
* Wait for the next release; your changes will appear in the release notes.

See [example](https://github.com/uktrade/data-hub-api/pull/1107/files).

### Remove the column from the databse

* Make sure you removed the field from the API and from django in a previous release and this has been deployed to production.
* Remove the column from the database:
    * Create an empty migration `./manage.py makemigrations <app> --empty --name=remove_<field>_from_database`.
    * Add the field copying the definition from a previous migration file and then immediately after remove it completely. See [example](https://github.com/uktrade/data-hub-api/blob/70eb77d76f5189f9476601ca1a5f118c9b7cbe5f/datahub/company/migrations/0035_remove_account_manager_column.py).
    * `./manage.py migrate`.
* Create a `.removal` and a `.db` newsfragment announcing the change.
* Open a PR and merge it into develop after it's been approved.
* Wait for the next release; your changes will appear in the release notes.

## How to rename a field

The process is similar to [the process for migrating a foreign key to a many-to-many field](./How&#32;to&#32;change&#32;the&#32;type&#32;of&#32;a&#32;field.md).

Differences include:

* the new field will need to, initially, be nullable (it can be made non-nullable if desired once it has been fully populated with data)

* a different Celery task (or management command) will need to be used for the one-off copy of historical data from the old field to the new field 
