from django.dispatch import Signal

order_paid = Signal()
order_completed = Signal()
order_cancelled = Signal()

quote_generated = Signal()
quote_accepted = Signal()
quote_cancelled = Signal()
