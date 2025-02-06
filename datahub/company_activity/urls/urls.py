from django.urls import include, path

urlpatterns = [
    path('stova-events/', include(('datahub.company_activity.urls.stova_urls',
         'stova-event'), namespace='stova-event')),
]
