# How to prepare a release

Commits to `main` are automatically deployed to dev and staging environments.

Deployments to production are done manually through Jenkins where a Git tag can be used.

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

5. Go to Jenkins and click on `Build with Parameters`.

6. Select `production` for the environment.

7. Type the `v<VERSION_NUMBER>` created in step `2` into the `Git_Commit` text field.

8. Press the `Build` button.

9. Create a GH release by clicking `Draft a new release` on the [releases page](https://github.com/uktrade/data-hub-api/releases).

The release title should be `v<VERSION_NUMBER>` and release notes can be created by clicking the `Auto-generate release notes` button.

10. After the Jenkins build has finished, publish the GH release.

11. Post the following message on the #data-hub slack channel, making sure to put the actual version number and link the release notes:

```
@here Data Hub API v<VERSION_NUMBER> is now live!
For more information see the release notes.
```