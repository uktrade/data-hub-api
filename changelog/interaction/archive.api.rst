``GET /v3/interaction`` and ``GET /v3/interaction/<uid>``: The following fields were added:

* ``archived`` - boolean - whether the interaction has been archived or not, 
  defaults to ``False``
* ``archived_on`` - datetime string, nullable - the datetime at which the interaction
  was archived
* ``archived_by`` - object, nullable - the Adviser that archived the interaction
* ``archived_reason`` - string, nullable - free-form text explaining the reason
  for archiving the interaction

These fields cannot be modified with PATCH or POST requests.

Two additional API endpoints were added:

``POST /v3/interaction/<uid>/archive`` - requires a ``"reason"`` parameter.  This
will archive an interaction with the supplied reason.

``POST /v3/interaction/<uid>/unarchive`` This will 'un-archive' an interaction.
