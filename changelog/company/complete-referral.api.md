A new endpoint, `POST /v4/company-referral/<ID>/complete`, was added for completing a company referral.

The request body is in the same format as `POST /v3/interaction`, except that the `company` field is not used as this comes from the referral object.
