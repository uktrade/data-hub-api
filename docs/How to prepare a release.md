# How to prepare a release


## Decide on the release type

You'll need to decide if the release is a major, minor or patch release.

As a general guide:

* if the new version contains _only_ non-breaking bug fixes, then it's a patch version
* if it contains breaking API changes, then it's a major version
* anything else is a minor version 

You can run `towncrier --draft --version draft` to generate a draft changelog, or [look at the difference between develop and master](https://github.com/uktrade/data-hub-api/compare/master...develop), to help you decide.

## Bump the version and update the changelog

Once you've reviewed the draft changelog and decided on the release type, you can create the changelog by running:

```shell
scripts/prepare_release.py <major|minor|patch>
```

<details>
<summary>What the command does</summary>
The command will:

- determine the new version number
- create a branch named `changelog/<version>`
- bump the version and update the changelog
- commit the changes
- push the branch
- open your browser window ready to create a PR
</details>

If the command succeeds, it will open your web browser ready to create a PR to merge `changelog/<version>` into 
`develop`.

Check the changelog preview is as expected, add at least two developers as reviewers and click 'Create pull request'.

When ready, merge `changelog/<version>` into `develop` and delete the merged branch.

## Create the release PR

Create and push a release branch from develop by running:

```shell
scripts/create_release_pr.py
```

<details>
<summary>What the command does</summary>
The command will:

- run `git fetch`
- create a branch `release/<version>` based on `origin/develop`
- push this branch
- open a web browser window to the create PR page for the pushed branch (with `master` as the base branch)
</details>

If the command succeeds, it will open your web browser ready to create a PR to merge `release/<version>` into `master`. 

Double-check that the details are correct and that the base branch is set to `master`.

Add at least two developers as reviewers and click 'Create pull request'.

After the PR has been reviewed, merge it into `master` and delete the merged branch.

## Deploy to staging

Following the merge of the release PR, the release will be automatically 
deployed to staging via Jenkins.

Check that everything looks fine before proceeding.

## Tag and publish the release on GitHub

The merging of the release PR will also trigger a GitHub Actions workflow
that will automatically publish the release on GitHub.

You can [check the status of the job on the Actions tab on GitHub](https://github.com/uktrade/data-hub-api/actions).

Once the job is complete, the release should appear [on the releases tab](https://github.com/uktrade/data-hub-api/releases).

(If something goes wrong, it’s also possible to run `scripts/publish_release.py` locally.
To do that you, you’ll need to [generate a GitHub personal access token](https://github.com/settings/tokens) with the `public_repo` scope.)

## Deploy to production
Deployment to production happens manually but after the release has been announced on Slack.

Post in the `#data-hub` slack channel the following (replacing `<version>` with the version number):

```
@here Data Hub API version <version> is ready to be deployed to production. Have a look at the release notes to see how this will affect you: https://github.com/uktrade/data-hub-api/blob/master/CHANGELOG.md.
Will deploy in 30 minutes or so if no objections.
```

If no objections are received, the release can be deployed to production.

In Jenkins, go to the _datahub_ tab, the _datahub-api_ project and click on _Build with Parameters_.

Type the following:
* **environment**: `production`
* **git commit**: `master`

Click on `build`, follow the deployment and check that everything looks fine after it finishes.
