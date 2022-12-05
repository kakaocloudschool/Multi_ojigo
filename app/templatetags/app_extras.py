from django import template

register = template.Library()


@register.filter
def calc_percent(value, arg):
    try:
        value = int(value)
        arg = int(arg)
        if arg:
            return round(value / (arg + value) * 100)
    except:
        pass
    return ""
