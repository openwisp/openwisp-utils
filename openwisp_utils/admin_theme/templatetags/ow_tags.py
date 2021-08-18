from django import template
from django.template.defaultfilters import stringfilter
from django.template.loader import get_template

register = template.Library()


@register.simple_tag
def ow_create_filter(cl, spec, total_filters):
    tpl = get_template(spec.template)
    return tpl.render(
        {
            'title': spec.title,
            'choices': list(spec.choices(cl)),
            'spec': spec,
            'show_button': total_filters > 4,
        }
    )


@register.filter
@stringfilter
def join_string(value):
    '''
    Can be used to join strings with "-" to make id or class
    '''
    return value.lower().replace(' ', '-')
