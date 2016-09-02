from django.contrib import admin
from django.contrib.admin import ModelAdmin

from api.models.chcompany import CHCompany
from api.models.company import Company
from api.models.contact import Contact
from api.models.interaction import Interaction


class CHCompanyAdmin(ModelAdmin):
    model = CHCompany

    list_display = ("company_number", "company_name")

    def add_view(self, *args, **kwargs):
        self.exclude = getattr(self, 'exclude', ())
        return super(CHCompanyAdmin, self).add_view(*args, **kwargs)

    def change_view(self, *args, **kwargs):
        self.exclude = getattr(self, 'exclude', ())
        return super(CHCompanyAdmin, self).change_view(*args, **kwargs)


admin.site.register(CHCompany, CHCompanyAdmin)
admin.site.register(Company)
admin.site.register(Contact)
admin.site.register(Interaction)
