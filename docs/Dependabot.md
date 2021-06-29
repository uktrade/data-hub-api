# Managing Dependabot PRs

This is the process we have identified for dealing with Dependabot PRs that saves developer time and CircleCI resource.

1. Create a new branch called `chore/dependencies-[yyyy-mm-dd]`, inserting today’s date.
2. Open each Dependabot PR and check that the tests have passed. Re-run any failing tests as the majority of failures are caused by timeouts or flakiness. Codecov failures can be ignored. If the PR contains any persistently failing tests, create a maintenance ticket for it and move on (these will be picked up as part of live support or maintenance sprint).
3. Once all tests have passed, edit the PR so that the base branch is the `chore/dependencies` one. You should now be able to merge the PR without needing to request reviews.
4. Repeat steps 2 and 3 until all Dependabot PRs are either merged or identified as needing further work.
5. After all the PRs have been merged, checkout the branch locally and carry out some basic smoke tests.
6. Checkout the local frontend and run the e2e tests to ensure they still pass.
7. Rebase the dependency branch against `develop` to remove all the merge commits, then push the changes and open a PR (you don't need to make a news fragment).
8. If you are satisfied that everything is in order and all the tests have passed, request reviews as normal.

If the Elasticsearch version has been updated, the version used in [the frontend e2e tests](https://github.com/uktrade/data-hub-frontend/blob/master/docker-compose.e2e.yml#L82) needs to be updated to match.
