``GET /v3/interaction`` and ``GET /v3/interaction/<uid>``: The following fields were added:

* ``state`` - string - one of ``"incomplete"``, ``"complete"`` or ``"cancelled"``, 
  defaults to ``"complete"``
* ``location`` - string - free text representing the location of a meeting
* ``meeting_uid`` - string - text representing the meeting's identifier in
  an external calendar

These can all be modified with ``PATCH`` requests.
