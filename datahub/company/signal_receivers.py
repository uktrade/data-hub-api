from django.dispatch import Signal

export_country_update_signal = Signal(providing_args=['instance', 'created', 'by'])
export_country_delete_signal = Signal(providing_args=['instance', 'by'])
