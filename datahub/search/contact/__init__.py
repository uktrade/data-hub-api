from .models import Contact

from ..apps import SearchApp


class ContactSearchApp(SearchApp):
    """SearchApp for contacts"""

    name = 'contact'
    plural_name = 'contacts'
    ESModel = Contact
