# How to generate Database Migrations

This is a brief introduction to familiarise anyone new to some of the patterns and pitfalls that may occur. There are many examples that can help you solve setting up a migration but nothing will serve you better than experience with this. Examples can be found within [datahub/dbmaintenance/management/commands](datahub/dbmaintenance/management/commands)

1. This utilises a well defined **Django command pattern** meaning you can execute what ever your file name is called as a command, externally and internally, utlising django e.g. `python manage.py <your_command_name>` or `docker-compose run api python manage.py <your_command_name>`

2. Make sure whatever is done can be rolled back or **audited** using the [django reversion](https://django-reversion.readthedocs.io/en/stable/) library. This does however come with its own limitations and is probably the main reason this document exists. Django reversion **does not support batch updates**, meaning you always need to do all Postgres updates innificiently through Python code sequentially one row at a time and cant support either a raw SQL or ORM multi update/create. As slow and inefficient as this seems, and it will be, the only thing that triggers changes on the reversion audit and middleware that listens for changes, is on single changes or commits.  

   ```python
           with reversion.create_revision():
               self.do_database_stuff()
               reversion.set_comment('Comment to identify database stuff')
   ```

3. You can execute the command manually, as described above or utilising a **Job Scheduler** as a [Celery](https://docs.celeryproject.org/en/stable/getting-started/introduction.html) task and so one should guarantee the proposed command is *idempotent*. If anything fails, you will need to be able to **rollback** all the changes, so make sure that this can be orchestrated through revision seamlessly and is well tested to make sure it is working.
