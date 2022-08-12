# 2. Replace Celery with RQ

Date: 2022-08-12

## Status

Accepted

## Context

Celery upgrades have been escalated by various security patches requiring later versions for resolving the relevent issues. The result of this has brought about an issue that has not been rectified, not for a lack of effort from several developers, even though the decision to delay doing this until almost everything that can be done to solve the Celery issue had been exhausted. There seemed to be a few obvious resolutions that were explored, but they turned out to be fruitless. The security fork has mitigated any security risks, but we are now stuck between a fork and a hard place, with no possibility to upgrade Celery.

## Decision

We investigated several queuing tools and decided on [RQ](https://python-rq.org/), mostly because of it's simplcity and the dedication to only Redis. Before starting with RQ, the team took the decision to make sure that there would be better monitoring with RQ, with the ability to measure success, and to make sure that the changes would be easier to understand, to make sure the team would be mapping as close as possible to Celery without breaking functionality. The first area to upgrade was the elastic data synchronization, the reason being that this area had exposed race conditions within developers environments, consistently when setting up local machines with docker, and the final reason, being that this is the heart of the system, dealing with many transactions which gets to stress test RQ with the part of the system that deals with the highest volume of queues on a regular basis.

## Consequences

After carefully monitoring the results of over 1.5 milllion RQ transactions, we have enough evidence to understand that RQ is a good choice for all the Celery Tasks that were replaced. The Grafana charts and logs helped understand the trail of things succeeding, the average speed at which most things ran and that this was measureably a success. The developers experiencing the race conditions have never had any problems since this was upgraded. The next few phases have been mapped out in [Jira](https://uktrade.atlassian.net/browse/TET-16) and will commence very soon, starting with cron scheduled jobs, the only risky part because of the relience on an alternative library. watch this space for an update.
