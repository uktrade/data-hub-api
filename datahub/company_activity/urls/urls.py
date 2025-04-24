from django.urls import include, path

urlpatterns = [
    path(
        'stova-events/',
        include(
            ('datahub.company_activity.urls.stova_urls', 'stova-event'),
            namespace='stova-event',
        ),
    ),
    path(
        'kings-award',
        include(
            ('datahub.company_activity.urls.kings_award_urls', 'kings-award'),
            namespace='kings-award',
        ),
    ),
]
