# Incremental Pull Requests

## Overview

Developing a large feature for the Data Hub backend API should be an incremental
process.  That is, small related chunks of code should be created and fed in to
the repository as Pull Requests incrementally until the feature is launched and
cleaned up.

## Why?

Building features incrementally in this way might seem to add overhead for the
developer building the feature.  Actually, there are a number of benefits:

- Each incremental step for the feature is peer reviewed in great detail; the
  chunks are much easier for other devs in the team to digest and give meaningful
  reviews for. This also allows us to better adhere to our goal of 400 additions
  or changes per Pull Request.
  **Note:** Take a look at the docs for [Code Review guidelines](./Code&#32;review&#32;guidelines.md) for
  more context here.
- We can ensure good test coverage for each chunk of the feature which might
  otherwise be masked by over-reaching functional tests.
- This approach promotes thinking ahead about the overall structure of a large
  feature - which might include some prototyping/spec work which can be shared
  and reviewed with peers. This should mean that structural problems and 
  roadblocks are flagged up sooner - before a large body of work has been 
  completed.
