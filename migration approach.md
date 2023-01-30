<!-- Start by writing a django query to get all users that belong to the below list of roles.

- Project manager,
- Project assurance,
- Client relationship manager
- Referral source Managers
- Trade Advisor
- Trade attaché

For each of these users, run another query to find those which have an active investment (how is this calculated?). Copy that user to a new list for users with active investments

For each user in the active investments list, run an update to add the `investment-notifications` feature flag group to them

For each of these users, run another query to find those which have an active export (how is this calculated?). Copy that user to a new list for users with active exports

For each user in the active exports list, run an update to add the `export-notifications` feature flag group to them

## Test users

User with no active investment
User with active investment
User with no active export
User with active export
User with active export and active investment
Users in each of the roles -->

Approach after discussions:

## Lead ITAs

`investment-notifications` feature group contains the `personalised-dashboard` feature flag, so anyone given this group will see the new personalised dashboard.

Ticket RR-637 identified a list of 118 lead ITAs, who were then given `export-notifications` only as this gave them the notification bell but not the personalised dashboard

There are 3 ITAs who also have the `investment-notifications` feature group and so will see the personalised dashboard page:

- bohdan.ratycz@trade.gov.uk
- kevan.reade@mobile.ukti.gov.uk
- rob.lewtas@tradesoutheast.com

This means only those 3 lead ITAs will be getting any notifications for investments, as the api checks the feature flag when calculating who to send notificaitions to (is this expected)

Rerunning the list of lead ITAs today (26/01), gives 5 new ITAs that weren't from the november ticket

- heather.crocker@mobile.ukti.gov.uk
- heather.martin@mobile.trade.gov.uk
- kathryn.nolan@trade.gov.uk
- louise.stock@mobile.ukti.gov.uk
- ranjana.abraham@mobile.ukti.gov.uk

Questions:

- How did these user's get assigned the `export-notifications`? Sql script or django migration?
- How did the reminder subscriptions get created for these users?
- Should we move the `personalised-dashboard` feature flag out of the `investment-notifications` group, so we can assign ITAs to this group without them needing to see the new dashboard? We could write a script to add `personalised-dashboard` to anyone who has the `investment-notifications` group before we remove it.
  - There are 617 advisors with the `investment-notifications` group
  - There are 50 advisors with the `personalised-dashboard` feature flag

## POST users

We have the list of users and their email address, write a script to loop through and add the `investment-notifications` and `export-notifications` groups. Depending on the outcome of moving `personalised-dashboard` out of the `investment-notifications` group, this would need to be added as well

There is an issue with the email matching if we went this way, taking the below as an example:
Aakaash Dev
POST CSV email: Aakash.Dev@fco.gov.uk
DH username: Aakaash.Dev@mobile.ukti.gov.uk
DH SSO email: aakaash.dev-3faaf3da@id.trade.gov.uk
DH contact email: Aakash.Dev@fco.gov.uk

Using the SQL from Jon, gives 6627 POST advisors out of a total of 16341

## All ITAs

Get a list of all ITAs
Get a list of all lead ITAs
