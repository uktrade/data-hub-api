from django.urls import path

from .views import IntelligentHomepageView

urlpatterns = [
    path('homepage/', IntelligentHomepageView.as_view(), name='intelligent-homepage'),
]
