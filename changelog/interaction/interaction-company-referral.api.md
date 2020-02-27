`GET /v3/interaction`, `GET /v3/interaction/<id>`: A `company_referral` field was added to responses. If interaction 
has been created as a result of complete referral, the field will have following structure:

```json
{
  ...
  "company_referral": {
    "id": <company_referral_id>,
    "subject": "company referral subject",
    "created_on": <datetime>,
    "created_by": <nested adviser with contact email and DIT team>,
    "recipient": <nested adviser with contact email and DIT team>
  }
}
```

Otherwise, the value will be `null`.
