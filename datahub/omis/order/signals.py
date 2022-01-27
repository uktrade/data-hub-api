import django.dispatch

"""
The `providing_args` argument has been deprecated and is no longer supported by Django.
All signals were using 'providing_args=['order']' unless mentioned otherwise.
"""

order_paid = django.dispatch.Signal()
order_completed = django.dispatch.Signal()
order_cancelled = django.dispatch.Signal()

quote_generated = django.dispatch.Signal()
quote_accepted = django.dispatch.Signal()

"""providing_args=['order', 'by']"""
quote_cancelled = django.dispatch.Signal()
