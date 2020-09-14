A new set of endpoints has been added to aid end to end testing. These endpoints are enabled when
`ALLOW_TEST_FIXTURE_SETUP` environment variable is set. These endpoints are not authenticated and
should not be used in an environment other than tests.

`POST /testfixtureapi/reset-fixtures/`: Removes all database objects except Metadata and resets to
the state in the `test_data.yaml` fixtures file.

`POST /testfixtureapi/create-user/`: Creates a new user and authenticates provided token. It expects payload
in the following format:

```
{
        "first_name": <first name>,
        "last_name": <last name>,
        "email": <email>,
        "dit_team_id: <DIT team id>,
        "sso_email_user_id": <sso email user id>,
        "token": <desired token>
}
```

`POST /testfixtureapi/load-fixture/`: Loads database fixture. It expects fixture payload in the following format:
```
{
    "fixture": [
        {
            "model": "company.advisor",
            "pk": "413a608e-84a4-11e6-ea22-56b6b6499622",
            "fields":
            {
                "email": "abc@def",
                "first_name": "First name",
                "last_name": "Last name",
                "dit_team": "162a3959-9798-e211-a939-e4115bead28a"
            }
        }
    ]
}
```
