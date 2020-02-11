`GET /v4/company-referral`, `POST /v4/company-referral`, `GET /v4/company-referral/<id>`: A read-only `closure_reason` field was added to responses If the referral is not closed, it will contain an empty string. If the referral is closed, it will have one of the following possible values:

- `unreachable`
- `insufficient_information`
- `wrong_recipient`
