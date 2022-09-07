# 1. Record architecture decisions

Date: 2022-08-12

## Status

Accepted

## Context

We need to record the architectural decisions made on this project.

## Decision

We will use Architecture Decision Records, as [described by Michael Nygard](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions).

We agreed that any new ADRs should first be raised in a dev huddle before they are put up for general review. This is to ensure that everyone has input on the proposed decision and to ensure that everyone is aware of it.

## Consequences

See Michael Nygard's article, linked above. For a lightweight ADR toolset, see Nat Pryce's [adr-tools](https://github.com/npryce/adr-tools). Install [Graphviz](https://marketplace.visualstudio.com/items?itemName=geeklearningio.graphviz-markdown-preview) to view generated Graphviz diagrams. Please note this can all be done manually, just follow the format.

```bash
brew install adr-tools
# Initialise a directory
adr init docs/architecture/decisions
# Generate a new ADR
adr new Replace Celery with RQ
```
