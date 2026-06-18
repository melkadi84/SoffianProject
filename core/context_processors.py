from core.models import Theme

def theme_processor(request):
    """
    Context processor that fetches the active visual Theme configurations
    and exposes it under the 'theme' context variable.
    """
    try:
        active_theme = Theme.objects.filter(is_active=True).first()
    except Exception:
        active_theme = None
        
    return {
        'theme': active_theme
    }

def cart_processor(request):
    """
    Exposes the count of items in the cart for header badge indicator.
    """
    cart = request.session.get('cart', {})
    total_items = 0
    if isinstance(cart, dict):
        for val in cart.values():
            try:
                total_items += int(val)
            except (ValueError, TypeError):
                pass
    return {
        'cart_item_count': total_items
    }

