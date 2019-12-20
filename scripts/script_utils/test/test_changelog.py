import pytest

from script_utils.changelog import extract_version_changelog

CHANGELOG_CONTENT = """# Data Hub API 24.0.0 (2019-12-10)


## Features

- **Companies** A setting `DNB_AUTOMATIC_UPDATE_LIMIT` was added which can be used to limit the
  number of companies updated by the `datahub.dnb_api.tasks.get_company_updates`
  task.

## Bug fixes

- **Companies** A bug was fixed to ensure that DNB company updates can be ingested over multiple
  pages from dnb-service.  Previously, the cursor value was not being extracted
  from the URL for the next page correctly.


# Data Hub API 23.2.0 (2019-12-02)


## Bug fixes

- **Companies** Merging two companies (via the admin site) now works when both companies are on
  the same company list.

## API

- **Investment** `GET /v4/dataset/investment-projects-dataset`: The `competing_countries` field
  was updated to return country names rather than ids
- **OMIS** `GET /v4/dataset/omis-dataset`: The field `quote__accepted_on` was added to the omis
  dataset endpoint


# Data Hub API 23.1.0 (2019-11-28)


## Removals

- The `init_es` management command has been removed. Please use `migrate_es` instead.

## Features

- The `migrate_es` management command was updated to handle the case when indexes don‘t already
  exist.

  Hence, the `init_es` command is no longer required and has been removed.


"""

V24_0_0_EXPECTED = """## Features

- **Companies** A setting `DNB_AUTOMATIC_UPDATE_LIMIT` was added which can be used to limit the
  number of companies updated by the `datahub.dnb_api.tasks.get_company_updates`
  task.

## Bug fixes

- **Companies** A bug was fixed to ensure that DNB company updates can be ingested over multiple
  pages from dnb-service.  Previously, the cursor value was not being extracted
  from the URL for the next page correctly."""


V23_2_0_EXPECTED = """## Bug fixes

- **Companies** Merging two companies (via the admin site) now works when both companies are on
  the same company list.

## API

- **Investment** `GET /v4/dataset/investment-projects-dataset`: The `competing_countries` field
  was updated to return country names rather than ids
- **OMIS** `GET /v4/dataset/omis-dataset`: The field `quote__accepted_on` was added to the omis
  dataset endpoint"""


V23_1_0_EXPECTED = """## Removals

- The `init_es` management command has been removed. Please use `migrate_es` instead.

## Features

- The `migrate_es` management command was updated to handle the case when indexes don‘t already
  exist.

  Hence, the `init_es` command is no longer required and has been removed."""


@pytest.mark.parametrize(
    'version,expected_result',
    [
        pytest.param(
            '9.9.9',
            None,
            id='no-match',
        ),
        pytest.param(
            '24.0.0',
            V24_0_0_EXPECTED,
            id='start-of-changelog',
        ),
        pytest.param(
            '23.2.0',
            V23_2_0_EXPECTED,
            id='middle-of-changelog',
        ),
        pytest.param(
            '23.1.0',
            V23_1_0_EXPECTED,
            id='end-of-changelog',
        ),
    ],
)
def test_extract_version_changelog(version, expected_result):
    """Test extract_version_changelog() for various cases."""
    assert extract_version_changelog(CHANGELOG_CONTENT, version) == expected_result
