class MismatchedRecordsException(Exception):
    """
    To indicate that 2 entities were mistakenly thought to be the same
    company. E.g. a Data Hub company record and a Worldbase record with
    different DUNS numbers.
    """
