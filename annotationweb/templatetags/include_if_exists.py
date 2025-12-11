from django import template
from django.template.loader import get_template, TemplateDoesNotExist

register = template.Library()


@register.simple_tag(takes_context=True)
def include_if_exists(context, template_name, *args, **kwargs):
    """
    Render template with context, but only if it exists. If it does not exist, return empty string.
    """
    try:
        template = get_template(template_name)
        return template.render(context.flatten())
    except TemplateDoesNotExist:
        return ''