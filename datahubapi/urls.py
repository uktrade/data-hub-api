from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers
from api.views.chcompanyviewset import CHCompanyViewSet
from api.views.companyviewset import CompanyViewSet
from api.views.contactviewset import ContactViewSet
from api.views.interationviewset import InteractionViewSet
from api.views.searchview import search


router = routers.DefaultRouter()
router.register(r'ch', CHCompanyViewSet)
router.register(r'company', CompanyViewSet)
router.register(r'contact', ContactViewSet)
router.register(r'interaction', InteractionViewSet)

urlpatterns = [
    url(r'^search$', search),
    url(r'^', include(router.urls)),
    url(r'^admin/', admin.site.urls),
]
