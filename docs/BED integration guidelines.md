# Introduction

The Department of International Trade provides information to the Cabinet Office for capturing business intelligence around interactions using CSV file imports.  The CSV file is then manually altered to service the requirements and formats needed by the BED system in order to synchronise interactions in a slightly different format, needing reconciliation on a quarterly basis for generating reports needed by the Cabinet Office. 

Both systems expose APIs that facilitate REST CRUD operations, therefore with the utilisation of *Celery*, this data synchronisation will occur as a short based daily operation, making sure this is always synchronised and ready anytime in an automated way.  

More information on this topic can be found 

- [Datahub to BED Integration, Interactions and Intelligence](https://uktrade.atlassian.net/wiki/spaces/CDS/pages/2279867249/Data+Hub+to+BED+Integration+Interactions+and+Intelligence)
- [Technical proposal](https://uktrade.atlassian.net/wiki/spaces/CDS/pages/2376171795/BED+Technical+Proposal)

# BED system basics

This is to help with basic site familiarisation of the BED system. 

1. Get invited or setup by an Administrator of BED.
2. Login and navigate to [reset the security token](https://loginhub--november.lightning.force.com/lightning/settings/personal/ResetApiToken/home) where you can generate a session id.
3. In conjunction with your email and password, can facilitate the BED environment settings explained in the environment variable configuration.
4. The [home sandbox](https://loginhub--november.lightning.force.com/lightning/page/home) help orient all the pages and content related to BED organization and interactions.
5. Datahub Companies are known as BED [Accounts](https://loginhub--november.lightning.force.com/lightning/o/Account/list?filterName=Recent).
6. Datahub Contacts are BED [Contacts](https://loginhub--november.lightning.force.com/lightning/o/Contact/list?filterName=Recent).
7. Datahub Interactions are BED [Events or Add Interactions](https://loginhub--november.lightning.force.com/lightning/o/Event__c/list?filterName=Recent).
8. BED data structures and mapping information can be found within the [Object Manager](https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/home).
   - [Account](https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/AccountBrand/Details/view)
   - [Contact](https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/Contact/Details/view)
   - [Add Interactions](https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/01I58000001EcAY/Details/view)
   - [Event Attendee](https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/01I58000001EcAX/Details/view)

