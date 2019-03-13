 The table ``interaction_interactionditparticipant`` table was added with the following columns:

- ``"id" bigserial NOT NULL PRIMARY KEY``

- ``"adviser_id" uuid NULL``

- ``"interaction_id" uuid NOT NULL``

- ``"team_id" uuid NULL``

 This is a many-to-many relationship table linking interactions with advisers.

 The table had not been fully populated with data yet; continue to use ``interaction_interaction.dit_adviser_id`` and ``interaction_interaction.dit_team_id`` for the time being.
