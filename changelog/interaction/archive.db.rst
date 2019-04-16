Four supporting fields were added to ``interaction_interaction`` for the 
purpose of allowing interactions to be archived:

* ``archived`` (boolean, nullable)
* ``archived_on`` (datetime string, nullable) 
* ``archived_by_id`` (uuid, nullable) - foreign key to ``company_adviser``
* ``archived_reason`` (string, nullable)
