`GET /adviser/`: A new query parameter, `dit_team__role`, was added. This filters results to 
advisers within a particular DIT team role, using ID lookup.

For example, `GET /adviser/?dit_team__role=<UUID>` returns
advisers that are in 'International Trade Team' roles.