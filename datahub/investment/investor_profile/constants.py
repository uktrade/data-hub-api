from enum import Enum

from datahub.core.constants import Constant


class RequiredChecksConducted(Enum):
    """Required checks conducted constants."""

    cleared = Constant(
        'Cleared',
        '02d6fc9b-fbb9-4621-b247-d86f2487898e',
    )
    issues_identified = Constant(
        'Issues identified',
        '9beab8fc-1094-49b4-97d0-37bc7a9de631',
    )
    not_yet_checked = Constant(
        'Not yet checked',
        '81fafe5a-ed32-4f46-bdc5-2cafedf828e8',
    )
    checks_not_required = Constant(
        'Checks not required',
        'e6f66f9d-ed12-4bfd-9dd0-ac7e44f35034',
    )


REQUIRED_CHECKS_THAT_NEED_ADDITIONAL_INFORMATION = [
    RequiredChecksConducted.cleared.value.id,
    RequiredChecksConducted.issues_identified.value.id,
]

REQUIRED_CHECKS_THAT_DO_NOT_NEED_ADDITIONAL_INFORMATION = [
    RequiredChecksConducted.not_yet_checked.value.id,
    RequiredChecksConducted.checks_not_required.value.id,
]
