A new table company_companyexportcountry was created.
It has foreign key fields ``company_id`` and ``country_id``,
a ``sources`` ArrayField indicating whether it is user-entered or
from an externally-sourced (or both), and a Boolean ``deleted`` field.