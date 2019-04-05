``name.keyword``, ``name.trigram`` and ``trading_names.trigram`` sub-fields were added to the ``company_field_with_copy_to_name_trigram``
field type in all search models. These will replace the existing ``name_trigram`` and ``trading_names_trigram`` sub-fields and allow the type of the ``name``
sub-field to be changed from ``keyword`` to ``text``.
