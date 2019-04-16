``GET /v3/interaction`` and ``GET /v3/interaction/<uid>``: The following fields were added:

* ``status`` - string - one of ``'draft'`` or ``'complete'``, defaults to 
  ``'complete'``
* ``location`` - string - free text representing the location of a meeting,
  defaults to ``''``

These can both modified with ``PATCH`` requests.

When creating or updating an interaction whose ``status='draft'``, both ``service``
and ``communication_channel`` are no longer required.
