# Managing Dependabot PRs

This is the process we have identified for dealing with Dependabot PRs that saves developer time and CircleCI resource.

1. Create a new branch called `chore/dependencies-[yyyy-mm-dd]`, inserting today’s date.
2. Open each Dependabot PR and check that the tests have passed. Re-run any failing tests as the majority of failures are caused by timeouts or flakiness. Codecov failures can be ignored.
3. Once all tests have passed, edit the PR so that the base branch is the `chore/dependencies` one. You should now be able to merge the PR without needing to request reviews.
4. Repeat steps 2 and 3 until all PRs are either merged or identified as needing further work. Any PRs with consistently failing tests can be passed to the Technical Excellence team if required.
5. After all the PRs have been merged, checkout the branch locally and carry out some basic smoke tests.
6. Checkout the local frontend and [run the e2e tests](https://github.com/uktrade/data-hub-frontend/blob/master/docs/Running%20tests.md#e2e-tests) to ensure they still pass.
7. Rebase the dependency branch against `develop` to remove all the merge commits, then push the changes and open a PR.
8. If you are satisfied that everything is in order and all the tests have passed, request reviews as normal.
9. Once merged, deploy to production as soon as possible.

If the OpenSearch version has been updated, the version used by [the e2e tests](https://github.com/uktrade/data-hub-frontend/blob/master/docker-compose.e2e.backend.yml#L48) needs to be updated to match.
