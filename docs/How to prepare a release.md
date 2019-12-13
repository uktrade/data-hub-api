# How to prepare a release


## Decide on the release type

You'll need to decide if the release is a major, minor or patch release.

As a general guide:

* if the new version contains _only_ non-breaking bug fixes, then it's a patch version
* if it contains breaking API changes, then it's a major version
* anything else is a minor version 

You can run `towncrier --draft --version draft` to generate a draft changelog and help you decide.

## Bump the version and update the changelog

Once you've reviewed the draft changelog and decided on the release type, you can create the changelog by running:

```shell
scripts/prepare_release.py <major|minor|patch>
```

The command will:

- determine the new version number
- create a branch named `changelog/<version>`
- bump the version and update the changelog
- commit the changes
- push the branch
- open your browser window ready to create a PR

If the command fails, review the error and investigate.

In your web browser, check the changelog preview, and then open a PR to merge `changelog/<version>` 
into `develop`.

Assign at least two developers for review.

When ready, merge `changelog/<version>` into `develop` and delete the merged branch.

## Prepare the release

Create and push a release branch from develop by running:

```shell
scripts/create_release_pr.py
```

The command will:

- run `git fetch`
- create a branch `release/<version>` based on `origin/develop`
- push this branch
- open a web browser window to the create PR page for the pushed branch (with `master` as the base branch)

Once your web browser has opened, double-check that the details are correct and that the base branch is set to `master`.

Add at least two developers as reviewers and click 'Create pull request'.

## Release to staging

After the PR has been reviewed, merge it into `master` and delete the merged branch.
The release will be automatically deployed to staging via Jenkins.
Check that everything looks fine before proceeding.

## Release to production
Releasing to production happens manually but after it has been announced and approved by the Live Services Team.

Post in the `#data-hub` slack channel the following (replace `<version>` with the version number and `<service-manager>` with the person resposible for approvals):

```
@here Data Hub API version <version> is ready to be deployed. Please check the release notes to know how this will affect you: https://github.com/uktrade/data-hub-api/blob/master/CHANGELOG.md. @<service-manager> Are you happy for us to release?
```

After the approval, the release can be deployed.

In jenkins, go to the _datahub_ tab, the _datahub-api_ project and click on _Build with Parameters_.

Type the following:
* **environment**: `production`
* **git commit**: `master`

Click on `build`, follow the deployment and check that everything looks fine after it finishes.

## Publish the release on GitHub

The final step is to publish the release on GitHub. To do this, you will need to [generate a GitHub personal access 
token](https://github.com/settings/tokens) with the `public_repo` scope.

Once you have this, you can either set it in the `GITHUB_TOKEN` environment variable, or enter it when prompted.

When you have a token, run:

```shell
scripts/publish_release.py
```

This will create and publish the release on GitHub and open it in your web browser. 

<details>
<summary>If you are unable to use the script</summary>

If you can‘t use the script for some reason, you can still manually create and publish the release.

In GitHub, [create a release](https://github.com/uktrade/data-hub-api/releases/new) with the following values:

* **Tag version**: `v<version>` e.g. `v6.3.0`
* **Target**: `master`
* **Release title**: `v<version>` e.g. `v6.3.0`
* **Describe this release**: copy/paste the notes from the compiled changelog.

And click on _Publish release_.

For more information see the [GitHub documentation](https://help.github.com/articles/creating-releases/).

</details>
