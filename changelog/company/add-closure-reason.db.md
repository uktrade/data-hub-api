A `"closure_reason" varchar(255) NOT NULL` column was added to the `company_referral_companyreferral` table. If the referral is not closed, it will contain an empty string. If the referral is closed, it can have the following possible values:

- `unreachable`
- `insufficient_information`
- `wrong_recipient`
