# How to prepare a release


## Decide on the new version number
The current format is `<major>.<minor>.<patch>`.

Start from [the latest](https://github.com/uktrade/data-hub-leeloo/blob/develop/CHANGELOG.md) and increase the number depending on if it's a major, a minor or a patch release.

## Update the changelog
Create a branch from develop:

```
git checkout develop && git pull
git checkout -b changelog-<version>
```

Compile the changelog:

```
towncrier --version <version>
```

Add and push the changes:

```
git add .
git commit -m 'Add changelog for <version>'
git push origin changelog-<version>
```

In GitHub, open a PR to merge `changelog-<version>` into `develop` and assign at least two developers for review.

When ready, merge `changelog-<version>` into `develop` and delete the merged branch.

## Prepare the release

Create a release branch from develop:

```
git checkout develop && git pull
git checkout -b release/<version>
```

Push the branch:

```
git push origin release/<version>
```

In GitHub open a PR to merge `release/<version>` into `master` and assign at least two developers for review.

## Release to staging

After the PR has been reviewed, merge it into `master` and delete the merged branch.
The release will be automatically deployed to staging via Jenkins.
Check that everything looks fine before proceeding.

## Release to production
Releasing to production happens manually but after it has been announced and approved by the Live Services Team.

Post in the `#data-hub` slack channel the following (replace `<version>` with the version number and `<service-manager>` with the person resposible for approvals):

```
@here Data Hub API version <version> is ready to be deployed. Please check the release notes to know how this will affect you: https://github.com/uktrade/data-hub-leeloo/blob/master/CHANGELOG.md. @<service-manager> Are you happy for us to release?
```

After the approval, the release can be deployed.

In jenkins, go to the _datahub_ tab, the _datahub-api_ project and click on _Build with Parameters_.

Type the following:
* **environment**: `production`
* **git commit**: `master`

Click on `build`, follow the deployment and check that everything looks fine after it finishes.

## Formalise the release

In GitHub, [create a release](https://github.com/uktrade/data-hub-leeloo/releases/new) with the following values:

* **Tag version**: `v<version>` e.g. `v6.3.0`
* **Target**: `master`
* **Release title**: `v<version>` e.g. `v6.3.0`
* **Describe this release**: copy/paste the notes from the compiled changelog.

And click on _Publish release_.

For more information see the [GitHub documentation](https://help.github.com/articles/creating-releases/).
