# How to change the type of a field

## Overview

Changing an API field can take a few weeks so please plan ahead with your team.

We currently use blue-green deployments with zero downtime (but with a shared database). This means that for some time an old instance of the application could have an active connection to the most up-to-date version of the database. Please implement your changes with this architecture design in mind.

## How to migrate a foreign key to a many-to-many field

This approach involves creating a new field coexisting with the existing field, gradually migrating logic to use the new field and finally removing the old field.

Each release remains compatible with the previous release, so that rolling (blue-green) deployments work smoothly, and the release can be rolled back if necessary. 

1. Open PR(s) to: 

    * add the new many-to-many field to the model, leaving the existing foreign key in place
  
    * make the existing API field write to the new many-to-many field (in addition to the existing foreign key)
  
    These changes ensure that any new data is written to both the old and new field (while leaving the API unchanged).
    
    [Example](https://github.com/uktrade/data-hub-api/pull/1404)

1. Release these changes and ensure the release is deployed to production.

1. If there is a significant amount of data to copy, run the [`dbmaintenance.tasks.copy_foreign_key_to_m2m_field` Celery task](https://github.com/uktrade/data-hub-api/blob/develop/datahub/dbmaintenance/tasks.py) manually in staging and production to copy historical data to the new field in small batches.

    (This is in order to avoid a long-running migration, as these tend to be problematic during deployments.)

1. Open a PR to:

    * add a migration that copies historical data from the old field to the new many-to-many field (where both are non-empty) so that local environments are updated
  
    [Example](https://github.com/uktrade/data-hub-api/pull/1423)
  
1. Release this and ensure the release is deployed to production.

1. Open PR(s) to: 

    * add the new many-to-many field to the API, writing to both the old and new field
  
    * make the old API field source its data from the new many-to-many field (but still write to both fields)
  
    * change any other logic and test data to use the new many-to-many-field (searching the code base for references)
  
    If the field was present in search models, the new field should also be added there (along with any filters etc. required). 
        
    [Example](https://github.com/uktrade/data-hub-api/pull/1415)

1. [Deprecate the old API field and database column.](./How&#32;to&#32;deprecate&#32;a&#32;field.md#document-deprecation)

1. Release these changes and ensure the release is deployed to production.

1. Remove the old field [from the API](./How&#32;to&#32;deprecate&#32;a&#32;field.md#how-to-remove-from-api) and [from the model and database](./How&#32;to&#32;deprecate&#32;a&#32;field.md#how-to-remove-column).

    Examples: [API removal](https://github.com/uktrade/data-hub-api/pull/1501), [state removal](https://github.com/uktrade/data-hub-api/pull/1556), [database removal](https://github.com/uktrade/data-hub-api/pull/1651)

### Additional considerations

If the field was editable from the admin site, you may want to temporarily make it read-only in the admin site until the migration to the new field is complete.  
