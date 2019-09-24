A new model CompanyExportCountry was created.
It has foreign key fields ``company`` and ``country``,
a ``source`` ArrayField indicating whether it is user-entered or
from an externally-sourced (or both), and a Boolean ``deleted`` field.