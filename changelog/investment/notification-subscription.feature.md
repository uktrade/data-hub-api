New endpoints have been added: `GET, POST /v3/investment/<project_pk>/notification` that manage email notifications subcription preferences.

An endpoint returns and accepts the following body:

```
{
    "estimated_land_date": ["30", "60"]
}
```

