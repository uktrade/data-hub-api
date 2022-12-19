# How to deactivate fixture data

## Overview

A lot of the data we use inside the API is hardcoded inside of .yaml files within each Django app. An example entry is shown here from the `specific_programmes.yaml` file

```
- model: investment.specificprogramme
  pk: 26881936-6823-4ad7-a6e0-41fb9f714dab
  fields: {disabled_on: null, name: "GREAT Investors - Capital Investment"}
```

If a request to remove this entry from being returned via the API was received, to avoid any breaking changes the entry should not be deleted. Instead, the `disabled_on` property should be set to the date the change is being made. This will allow any existing DB records to continue to work as the reference to the primary key still exists, but the value will be removed from any API GET requests for this data.

The resulting entry in the .yaml would look like this

```
- model: investment.specificprogramme
  pk: 26881936-6823-4ad7-a6e0-41fb9f714dab
  fields: {disabled_on: '2022-12-19T11:25:03Z', name: "GREAT Investors - Capital Investment"}
```