from enum import Enum

from datahub.core.constants import Constant


class Programme(Enum):
    """Programme constants."""

    great_branded = Constant('Great Branded', '3117da1b-ac76-4b03-af7e-2487d931491c')
    great_challenge_fund = Constant('Great Challenge Fund', '1abe5563-6482-41d8-b566-6a9ee9e37c5f')
    grown_in_britain = Constant('Grown in Britain', 'd352a68f-aaf4-4c43-b39d-9bca67a8322e')


class LocationType(Enum):
    """Location type constants."""

    hq = Constant('HQ', 'b71fa81c-0c22-44c6-ab6f-13b9e045dc10')
    post = Constant('Post', '6043fe88-9fc4-428e-8243-a20076e5c811')


class EventType(Enum):
    """Event type constants."""

    seminar = Constant('Seminar', '771f654d-e6b1-4fad-8a89-b6ac44147830')
    exhibition = Constant('Exhibition', '2fade471-e868-4ea9-b125-945eb90ae5d4')
