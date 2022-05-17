## Introduction

[RQ (_Redis Queue_)](https://python-rq.org/) is a simple Python library for queueing jobs and processing them in the background with workers. It is backed by Redis and it is designed to have a low barrier to entry.

This document will help you to setup monitoring locally, to see any statistics like failures, successes, average duration and when most things were executed, as well as the queues defined for RQ.

The core service for facilitating RQ exported information is [RQ exporter](https://github.com/mdawar/rq-exporter). This will run on localhost:9726 to facilitate any RQ monitoring as data source. The configuration for the environment variables can be overridden, see more information at [Environment variable configuration](https://github.com/mdawar/rq-exporter#configuration). The datasource will be setup through _Prometheus_.

## Environment

**NOTE**: If you have a new or flushed docker system make sure you run `docker-compose -f docker-compose.yml -f docker-compose-rq-monitor.yml up --build` to build all the images or simply run `docker compose up --build` to build the core dependencies.

- Starting all the services `make start-rq-mon`
- Stopping all the services `make stop-rq-mon`
