from enum import Enum

from datahub.core.constants import Constant


class Programme(Enum):
    """Programme constants."""

    great_branded = Constant('Great Branded', '3117da1b-ac76-4b03-af7e-2487d931491c')
    grown_in_britain = Constant('Grown in Britain', 'd352a68f-aaf4-4c43-b39d-9bca67a8322e')


class LocationType(Enum):
    """Location type constants."""

    hq = Constant('HQ', 'b71fa81c-0c22-44c6-ab6f-13b9e045dc10')


class EventType(Enum):
    """Event type constants."""

    seminar = Constant('Seminar', '771f654d-e6b1-4fad-8a89-b6ac44147830')
