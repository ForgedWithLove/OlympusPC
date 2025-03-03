from django import template
from pc_configurator.models import Manufacturer

register = template.Library()

@register.filter
def bool_to_str(bool_value):
    return 'Да' if bool_value else 'Нет'
    

