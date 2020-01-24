A new `company_referral_companyreferral` table was added to hold referrals of companies between DIT advisers.

The table has the following columns:

- `"id" uuid NOT NULL PRIMARY KEY`
- `"created_on" timestamp with time zone NULL`
- `"modified_on" timestamp with time zone NULL`
- `"status" varchar(255) NOT NULL`
- `"completed_on" timestamp with time zone NULL`
- `"subject" varchar(255) NOT NULL`
- `"notes" text NOT NULL`
- `"company_id" uuid NOT NULL`
- `"completed_by_id" uuid NULL`
- `"contact_id" uuid NULL`
- `"created_by_id" uuid NULL`
- `"modified_by_id" uuid NULL`
- `"recipient_id" uuid NOT NULL`
