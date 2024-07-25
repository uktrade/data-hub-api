# Deployments

Commits to `main` are automatically deployed to dev and staging environments.

Deployments to UAT and production are done manually through Copilot/platform-helper where a Git tag must be used.

## Deploying to production
1. Post a message into the #data-hub-core-dev channel saying that you want to do a Data Hub API release and ask if there are any objections. If no objections, proceed with the following steps.

2. Create a GIT tag `git tag v<MAJOR>.<MINOR>.<PATCH>`, e.g. `v5.1.2` pointing to the latest `main`.

   | Release type      | When to increase                                                                         |
   | ----------------- | ---------------------------------------------------------------------------------------- |
   | Major (**1**.0.0) | When a change requires modifications to the infrastructure, e.g. NodeJS version upgrade. |
   | Minor (0.**1**.0) | When a release contains at least one new feature.                                        |
   | Patch (0.0.**1**) | When a release contains only fixes.                                                      |

You can use the [GitHub comparison tool](https://github.com/uktrade/data-hub-api/compare) to figure out what changes have been made since the last release. You can find out the latest release tag number from [here](https://github.com/uktrade/data-hub-api/releases).

3. Push the tag to the remote - `git push origin v<VERSION_NUMBER>`.

4. Check that the tag worked by using the [GitHub comparison tool](https://github.com/uktrade/data-hub-api/compare) again to compare main to the new tag. If done correctly, there should be no difference. 

5. Create a GH pre-release by clicking `Draft a new release` on the [releases page](https://github.com/uktrade/data-hub-frontend/releases).

The release title should be `v<VERSION_NUMBER>` and release notes can be created by clicking the `Auto-generate release notes` button.

Check that the release notes generated contain what you expect to be deployed to production.

6. Follow the [deployment instructions in the Playbook](https://readme.trade.gov.uk/docs/playbooks/datahub.html#deployment).

7. After the DBT Platform deployment has finished, go to Data Hub production FE and API and check that everything is working correctly.

8. Change the GH pre-release to an actual release.

9. Post the following message on the #data-hub slack channel, making sure to put the actual version number and link the release notes:

```
@here Data Hub API v<VERSION_NUMBER> is now live!
For more information see the release notes.
```