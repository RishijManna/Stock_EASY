# accounts/templatetags/form_extras.py
from django import template
from django.utils.safestring import mark_safe
from django.forms.boundfield import BoundField

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    """
    Safely add CSS classes to a Django form field. If `field` is already a string,
    just return it unchanged to avoid AttributeError.
    """
    if isinstance(field, BoundField):
        # copy existing attrs and append classes
        attrs = field.field.widget.attrs.copy()
        prev = attrs.get('class', '')
        attrs['class'] = (prev + ' ' + (css or '')).strip()
        return field.as_widget(attrs=attrs)
    # If it's already rendered HTML or a plain string, return as-is
    return mark_safe(field)
