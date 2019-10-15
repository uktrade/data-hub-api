from importlib import import_module

# The Django autodiscover logic will import datahub.company.admin automatically, but not the
# modules contained in this package. Hence, we need to import all this package's modules
#
# In some cases, there is only registration code and no classes to import (e.g. the metadata
# module). So we import whole modules for all contained modules, and use import_module() to avoid
# creating unreferenced names (as it wouldn't make sense to add them to __all__).

import_module('datahub.company.admin.adviser')
import_module('datahub.company.admin.ch_company')
import_module('datahub.company.admin.company')
import_module('datahub.company.admin.company_export_country')
import_module('datahub.company.admin.contact')
import_module('datahub.company.admin.metadata')
