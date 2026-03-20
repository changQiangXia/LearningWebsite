import re

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def highlight_terms(value, terms):
    text = conditional_escape(value or "")
    if not text or not terms:
        return text

    highlighted = str(text)
    for term in terms:
        if not term:
            continue
        pattern = re.compile(re.escape(str(term)), flags=re.IGNORECASE)
        highlighted = pattern.sub(
            lambda match: f'<mark style="background:#fff3a3; padding:0 0.1rem;">{match.group(0)}</mark>',
            highlighted,
        )
    return mark_safe(highlighted)
