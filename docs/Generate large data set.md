# Generate large data set for testing

The below instructions explain how you can quickly generate a large data set for testing purposes.

## Generator script

A generator script has been included in the project root directory. To use it, simply execute the script on either your local or docker instance of the API:

```
python data_generator.py
```

> Note, the script uses the `config.settings.local` settings module for the Django application.

You can set how many Advisers/Companies/Contacts are generated by altering the value of the call to `advisers = AdviserFactory.create_batch(1800)`

The script creates Advisers, Companies, and Contacts without synchronising these with Open Search to speed up the process. Once the script has completed update the Open Search index (see below).

## Update Open Search

From the command line (either on the local or docker instance of the API) start the Open Search synchronisation by running:

```
python manage.py sync_search
```

You should be able to see its progress by monitoring the rq_long and rq_short workers.
