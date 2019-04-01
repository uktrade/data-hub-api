A number of supporting fields were added to ``interaction_interaction`` for the 
purpose of recording meetings:

* ``state`` (text) - one of ``"incomplete"``, ``"complete"`` or ``"cancelled"``, 
  defaults to ``"complete"``
* ``location`` (text, nullable) - free text representing the location of a meeting
* ``meeting_uid`` (text, unique, nullable) - text representing the meeting's 
  identifier in an external calendar
  
