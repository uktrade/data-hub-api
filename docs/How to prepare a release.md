# How to prepare a release


## Decide on the new version number
The current format is `<major>.<minor>.<patch>`.

Start from [the latest](https://github.com/uktrade/data-hub-leeloo/blob/develop/CHANGELOG.rst) and increase the number depending on if it's a major, a minor or a patch release.

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

## Release

After the PR has been reviewed, merge it into `master` and delete the merged branch.
The release will be automatically deployed to staging via Jenkins.
Releasing to production has to happen manually after it's been tested on staging and approved by the Live Services team.

## Formalise the release

In GitHub, [create a release](https://github.com/uktrade/data-hub-leeloo/releases/new) with the following values:

* **Tag version**: `v<version>` e.g. `v6.3.0`
* **Target**: `master`
* **Release title**: `v<version>` e.g. `v6.3.0`
* **Describe this release**: copy/paste the notes from the compiled changelog after converting the rst text into md using something like [pandoc](http://pandoc.org/try/).

And click on _Publish release_.

For more information see the [GitHub documentation](https://help.github.com/articles/creating-releases/).

## Tell everyone

Post in the `#data-hub` slack channel the following (replace `<version>` with the version number):

```
@here Data Hub API has been updated to version <version>. Please check the release notes to know how this will affect you: https://github.com/uktrade/data-hub-leeloo/blob/master/CHANGELOG.rst.
```
