## Introduction

[RQ (_Redis Queue_)](https://python-rq.org/) is a simple Python library for queueing jobs and processing them in the background with workers. It is backed by Redis and it is designed to have a low barrier to entry.

From the rq docs:

> A job is a Python object, representing a function that is invoked asynchronously in a worker (background) process. Any Python function can be invoked asynchronously, by simply pushing a reference to the function and its arguments onto a queue. This is called enqueueing.

### Generic concepts to understand:
- Workers
    - These are services (when running on GovPaaS) or containers (when running locally on Docker). They loop through their assigned queues looking for jobs to process. They are started from the scripts `long-running-worker.py` and `short-running-worker.py`.
- Queues
    - These are just like real life queues, identified by unique strings (e.g. ‘long-running’). Jobs can be ‘enqueued’  on them, to be run asynchronously in order.
- Jobs
    - A job represents a function to be called by the worker.

### Datahub specific code:
![job scheduler sequence diagram](jobSchedulerSequence.png)

- [Job_scheduler](https://github.com/uktrade/data-hub-api/blob/main/datahub/core/queues/job_scheduler.py)
    - This is the main interface to enqueue jobs. Based on the arguments it will either call DataHubScheduler’s `enqueue` or `cron` functions. 
- [DataHubScheduler](https://github.com/uktrade/data-hub-api/blob/main/datahub/core/queues/scheduler.py)
    - This is the class to ensure that we start workers and enqueue or schedule jobs in a consistent way.

## How to schedule a job

First decide if it's a one off job, or you want to it to repeat regularly.

### enqueue 
(schedule to run when it reaches the front of a queue)
1. Call `job_scheduler()` with the function you want to get called, e.g. `job_scheduler(hello_world)` some more [examples are in the tests](https://github.com/uktrade/data-hub-api/blob/main/datahub/core/test/queues/test_job_scheduler.py)
1. You can configure args and kwargs for the function, and override the default queue, set intervals etc. 

### cron
(repeat job at set intervals/times)
1. The same as step 1 above, but pass in a `cron` value and it will repeat accordingly. There are [constants for some often used cron values.](https://github.com/uktrade/data-hub-api/blob/main/datahub/core/queues/cron_constants.py)


## Monitoring RQ locally

This will allow you to monitor RQ locally, to see statistics like failures, successes, average duration and when most things were executed, as well as the queues defined for RQ.

The core service for facilitating RQ exported information is [RQ exporter](https://github.com/mdawar/rq-exporter). This will run on localhost:9726 to facilitate any RQ monitoring as data source. The configuration for the environment variables can be overridden, see more information at [Environment variable configuration](https://github.com/mdawar/rq-exporter#configuration). The datasource will be setup through _Prometheus_.

### Environment

**NOTE**: If you have a new or flushed docker system make sure you run `docker-compose -f docker-compose.yml -f docker-compose-rq-monitor.yml up --build` to build all the images or simply run `docker compose up --build` to build the core dependencies.

- Starting all the services `make start-rq-mon`
- Stopping all the services `make stop-rq-mon`

## Troubleshooting

Troubleshooting
1. Jobs are being queued but not started

    Means the service to work those queues has not been started or the started queue is blocking that from being started.

1. Jobs are failing
    ???

1. Scheduled jobs are being repeated/run too many times

    Cron jobs need to be canceled or they will run forever even if the app has restarted/been redeployed. Hence the `cancel_existing_cron_jobs` in the `cron-scheduler`. 