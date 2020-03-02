def format_expected_adviser(adviser):
    """
    Formats Adviser object into format expected to be returned by
    `NestedAdviserWithEmailAndTeamField`.
    """
    if not adviser:
        return None

    return {
        'contact_email': adviser.contact_email,
        'dit_team': {
            'id': str(adviser.dit_team.pk),
            'name': adviser.dit_team.name,
        },
        'id': str(adviser.pk),
        'name': adviser.name,
    }
