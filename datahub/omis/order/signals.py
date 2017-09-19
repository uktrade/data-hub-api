import django.dispatch


quote_generated = django.dispatch.Signal(providing_args=['order'])
