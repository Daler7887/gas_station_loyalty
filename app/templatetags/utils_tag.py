from django import template
from app.utils import *

register = template.Library()

@register.filter()
def index(l, i):
    return l[i]