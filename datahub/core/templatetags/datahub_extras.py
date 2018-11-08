from django import template
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.admin.utils import quote
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def verbose_name_for_count(count, model_meta):
    """
    Template tag similar to the pluralize filter but for model verbose names.

    Picks verbose_name or verbose_name_plural from a model _meta object based on a count passed
    in.

    Usage example (in a template):

      {% verbose_name count model_opts %}
    """
    return model_meta.verbose_name if count == 1 else model_meta.verbose_name_plural


@register.filter
def admin_change_url(obj):
    """
    Template filter to generate the URL to the admin change page for a model object.

    Usage example:

      <a href="{{ target_company|admin_change_url }}">{{ target_company }}</a>
    """
    route_name = admin_urlname(obj._meta, 'change')
    return reverse(route_name, args=(quote(obj.pk),))


@register.filter
def admin_change_link(obj, target_blank=False):
    """
    Template filter to generate the URL to the admin change page for a model object.

    Usage examples:

      Normal anchor tag:
      {{ target_company|admin_change_link }}

      With target="_blank":
      {{ target_company|admin_change_link:True }}
    """
    extra_attrs = ' target="_blank"' if target_blank else ''
    return format_html(
        '<a href="{url}"{extra_attrs}>{obj}</a>',
        url=admin_change_url(obj),
        extra_attrs=mark_safe(extra_attrs),
        obj=obj,
    )
