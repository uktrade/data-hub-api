from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers
from api.views.chcompanyviewset import CHCompanyViewSet
from api.views.companyviewset import CompanyViewSet
from api.views.searchview import search


router = routers.DefaultRouter()
router.register(r'ch', CHCompanyViewSet)
router.register(r'company', CompanyViewSet)

urlpatterns = [
    url(r'^search$', search),
    url(r'^', include(router.urls)),
    url(r'^admin/', admin.site.urls),
]
