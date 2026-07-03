from django import template
from django.utils.translation import get_language
from core.translations import TRANSLATIONS

register = template.Library()

@register.simple_tag
def t(text, *args):
    """
    Template tag to translate user interface text into the currently active language context
    using our local dictionary. Supports Python string formatting args.
    
    Usage:
        {% load translate_tags %}
        {% t "Store" %}
        {% t "Showing {} available products" product_count %}
    """
    lang = get_language() or 'en'
    # Strip regional settings if any (e.g. 'en-us' -> 'en')
    lang_short = lang.split('-')[0].lower()
    
    translated = TRANSLATIONS.get(lang_short, {}).get(text, text)
    
    if args:
        try:
            return translated.format(*args)
        except Exception:
            return translated
            
    return translated


@register.filter
def currency(value):
    """
    Formats the given value as EGP currency according to bilingual context.
    Usage:
        {{ product.price|currency }}
    """
    if value is None:
        return ""
    try:
        val_float = float(value)
    except (ValueError, TypeError):
        return value
        
    lang = get_language() or 'en'
    lang_short = lang.split('-')[0].lower()
    
    # Format with two decimal places
    formatted_val = f"{val_float:,.2f}"
    
    if lang_short == 'ar':
        return f"{formatted_val} ج.م"
    return f"EGP {formatted_val}"


from django.utils.safestring import mark_safe

@register.simple_tag
def render_stars(rating):
    try:
        r = float(rating)
    except (ValueError, TypeError):
        r = 0.0
    full_stars = min(5, max(0, int(r)))
    half_star = 1 if (r - full_stars) >= 0.25 and full_stars < 5 else 0
    empty_stars = max(0, 5 - full_stars - half_star)
    
    html = ""
    for _ in range(full_stars):
        html += '<i class="bi bi-star-fill"></i>'
    if half_star:
        html += '<i class="bi bi-star-half"></i>'
    for _ in range(empty_stars):
        html += '<i class="bi bi-star"></i>'
    return mark_safe(html)


