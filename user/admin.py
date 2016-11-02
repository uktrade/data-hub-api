from django.contrib import admin

from reversion.admin import VersionAdmin

from . models import Advisor

admin.site.register(Advisor, VersionAdmin)
