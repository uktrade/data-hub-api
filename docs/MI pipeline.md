# MI pipeline

## Overview

MI pipeline is an extract, transform and load process that loads Data Hub investment projects 
(with any personally identifiable information removed) into the external database (referred to as MI database).
The process has been implemented in the `mi_dashboard` Django application.

The data model of the MI database is being managed from that application.

Data model *must not* contain any personally identifiable information under any circumstances.

The MI database is being used by the dashboard solution as a read-only data source.

Pipeline process runs as a celery task every night at 1 am. 

## Deployment

Upon deployment, the data model of MI database is not automatically migrated. A developer must ensure that Data Hub 
will operate while the data has not yet been migrated - this, however, shouldn't typically be a problem as the process 
runs only once during each night.

## How to update

Before updating `InvestmentProject` or `MIInvestmentProject` models developer *should* consult appropriate team and 
assess the impact a change would make to the MI dashboards using `MIInvestmentProject` table as their data source.
If a change doesn't affect already defined columns and data transformations, then that shouldn't be an issue.
A Developer should at least make sure that the tests defined in the `mi_dashboard` application pass. 

In the event of changing the MI investment project model (`MIInvestmentProject`), a developer should run a migration 
in the environment where the Data Hub has been deployed by issuing the following command:

```
./manage.py migrate --database mi
```

Once this has finished, a developer should run the pipeline process to ensure the data in MI database is up to date:

```
./manage.py run_pipeline
```

## Database

When making changes to `MIInvestmentProject` table in MI database, a developer must take into account that the underlying 
RDBMS is PostgreSQL 9.6.
