/*
    Tests for regular expression logic can be found @
    Test at https://regex101.com/r/yckIVj/1
 */
update company_company cmpy
set address_postcode = sub.fix
from
	(
		select company_fix.id,(array_to_string(regexp_matches(replace(company_fix.address_postcode, ' ', ''),'(\d{5}-\d{4})|(\d{5}\s–\s\d{4})|(\d{5}\s–\s\d{4})|(\d{9})|(\d{5})|(\d{1}\s\d{4})''g'),';')) as fix from company_company company_fix
	) as sub
where
	cmpy.address_country_id = '81756b9a-5d95-e211-a939-e4115bead28a'
	and sub.id = cmpy.id
	and cmpy.address_postcode ~ e'^\\d{3}' = false
	and sub.fix is not null
