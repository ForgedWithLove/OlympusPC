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
    

