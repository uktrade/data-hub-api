from django.dispatch import Signal

"""
The `providing_args` argument has been deprecated and is no longer supported by Django.
The contents has been preserved for references.
"""

"""providing_args=['instance', 'created', 'by']"""
export_country_update_signal = Signal()

"""providing_args=['instance', 'by']"""
export_country_delete_signal = Signal()
