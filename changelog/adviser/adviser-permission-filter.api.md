`GET /adviser/`: A new query parameter, `permissions__has`, was added. This filters results to 
advisers with a particular permission.

For example, `GET /adviser/?permissions__has=company_referral.change_companyreferral` returns
advisers that are allowed to update company referrals. 
