from django.contrib import admin

from reversion.admin import VersionAdmin

from . models import User

admin.site.register(User, VersionAdmin)
