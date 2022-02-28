"""
Generic functionality related to 'metadata'.

Metadata is used here to mean reference data, such as a list of countries or a list of company
types (see https://en.wikipedia.org/wiki/Reference_data).

Metadata models that are generic (e.g. Country) are placed in this app, but those specific
to a certain Django app (e.g. BusinessType are specific to companies) are usually placed in
that specific Django app.

Metadata models are registered within `metadata` modules in each Django app. This automatically
creates views for that model under the `/v4/metadata/` URL path.
"""

from django.utils.module_loading import autodiscover_modules


def autodiscover():
    """Loads the `metadata` module in each individual apps."""
    autodiscover_modules('metadata')
