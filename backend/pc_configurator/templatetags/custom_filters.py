from django import template
import json
from pc_configurator.models import Manufacturer

register = template.Library()

@register.filter
def bool_to_str(bool_value):
    return 'Да' if bool_value else 'Нет'

@register.filter
def get_json_value(json_str, key):
    return json.loads(json_str)[key]

@register.filter
def key_in_json(json_str, key):
    return True if key in json.loads(json_str).keys() else False

@register.filter
def get_json_keys(json_str):
    return json.loads(json_str).keys()

@register.filter
def array_output(array):
    string = ''
    length = 32
    for index, value in enumerate(array):
        if length - len(value) < 0:
            string += f'\n{value}, ' if index != len(array) - 1 else f'\n{value}'
            length = 32 - len(value)
        else:
            string += f'{value}, ' if index != len(array) - 1 else f'{value}'
            length -= len(value)
    return string
    

@register.filter
def coolant_output(coolant):
    if coolant == 'air':
        return 'Воздушный'
    elif coolant == 'liquid':
        return 'Жидкостный'
    else:
        return coolant
    

