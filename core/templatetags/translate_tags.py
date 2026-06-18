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

