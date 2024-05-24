from enum import Enum

from datahub.core.constants import Constant

EMAIL_MAX_DAYS_TO_RESPONSE_THRESHOLD = 7
EMAIL_MAX_WEEKS_AUTO_RESEND_THRESHOLD = 3
EMAIL_MAX_TOKEN_ISSUED_WITHIN_RESPONSE_THRESHOLD = 4

EXPORT_WINS_LEGACY_ID_START_VALUE = 2000000


class TeamType(Enum):
    """Team Type constants."""

    team = Constant('Trade (TD or ST)', 'a4839e09-e30e-492c-93b5-8ab2ef90b891')
    investment = Constant('Investment (ITFG or IG)', '42bdaf2e-ae19-4589-9840-5dbb67b50add')
    dso = Constant('DSO', 'c2d215e2-d564-4c50-b209-ec838eef761d')
    obn = Constant('Overseas Business Network', '17f95045-63b4-489d-9af8-7246e6ab370e')
    other = Constant('Other HQ Team', 'bbb7fad4-417c-411e-a40a-11184b0c635d')
    itt = Constant('International Trade Team', '1f6eccf9-289a-450b-a4af-b75600ea521b')
    post = Constant('Overseas Post', '6e798633-83da-4597-8e9a-9bb033ca06a4')
    tcp = Constant('Trade Challenge Partners (TCP)', 'f7006548-9ef0-4c4e-bc60-1b7ca40ff75b')
    trade = Constant('Export Support Services', '24823128-f9e6-4877-a12f-4995f8b525d8')
