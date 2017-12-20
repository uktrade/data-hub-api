from django import template
from django.contrib.admin.templatetags.admin_modify import submit_row

register = template.Library()


@register.inclusion_tag('admin/order/submit_line.html', takes_context=True)
def order_submit_row(context):
    """
    Extend the default `submit_row` by adding an extra flag to show the cancel
    button.
    """
    context = submit_row(context)
    context['show_cancel'] = context['show_save'] and context['change']
    return context
