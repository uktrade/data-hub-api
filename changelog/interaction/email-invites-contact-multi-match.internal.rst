The meeting email invites ingestion parsing logic was adjusted to use a new ``max_interactions``
strategy for finding a contact.  This ensures that when multiple contacts are
found which match the same email address, the contact with the most interactions
attributed to it takes precedence.  It's an imperfect solution, but acts as a best
guess for imperfect data.
