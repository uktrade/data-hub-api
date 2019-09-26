# Managing dependencies

## Overview

Dependencies in this project are managed using 
[pip-compile and pip-sync (from pip-tools)](https://github.com/jazzband/pip-tools).

Direct dependencies are specified in `requirements.in` (which is manually 
edited). These are pinned to a specific version to make it easier to control 
and track upgrades to direct dependencies. A small number of indirect dependencies are also
included in `requirements.in` where we have previously had breakages caused by updates to
those libraries.

`requirements.txt` is a lock file generated using pip-compile and should not be manually edited.

## Installing dependencies

Dependencies should always be installed using `requirements.txt`. The first time you do this, 
you should run:

```shell
pip install -r requirements.txt
````
 
After that, you can run `pip-sync` instead.
(Note that pip-sync will also remove any installed dependencies that are not specified in the
lock file, such as removed dependencies or packages manually installed using pip.)

## How to add a new dependency

1. Add the package to the relevant section in `requirements.in`, specifying a particular version
(typically the latest at time of adding).

2. Run `pip-compile --upgrade --output-file requirements.txt requirements.in` to regenerate 
`requirements.txt`. Note: This will also update indirect dependencies.

3. Run `pip-sync` to install the new locked dependencies locally. (You can also use 
`pip install -r requirements.txt`, but that may leave behind redundant packages that 
have been removed which can cause problems.)

4. Commit the changes as part of your feature branch.

## How to upgrade dependencies

1. Check for out-of-date dependencies. You can use [piprot](https://github.com/sesh/piprot) for 
this by running `piprot -o requirements.in`. Alternatively, you can use pip 
by running `pip list -o`.

2. Update the versions in `requirements.in` to the new desired versions. Make sure you check 
the change logs for dependencies that are being updated in case they have any breaking changes.  

3. Run `pip-compile --upgrade --output-file requirements.txt requirements.in` to regenerate 
`requirements.txt`. Note that this will also update indirect dependencies.

4. Run `pip-sync` to install the new locked dependencies locally. (You can also use 
`pip install -r requirements.txt`, but that may leave behind redundant packages that 
have been removed which can cause problems.)

5. Commit the changes to a new branch, along with a brief [news fragment](../changelog/README.md) 
(unless something significant was updated, this can just say 'Various dependencies were updated').

6. Create a PR. Include links to the change logs for dependencies in `requirements.in` that 
were updated to make it easier for other developers to have a look at them. 

   [Example of such a PR.](https://github.com/uktrade/data-hub-leeloo/pull/1171)
