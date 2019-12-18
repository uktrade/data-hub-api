A bug was fixed that resulted in a runtime error in the `get_company_updates` celery task.

The error happened when `get_company_updates` tried to wait on the results of sub-tasks in order to produce an audit log.
