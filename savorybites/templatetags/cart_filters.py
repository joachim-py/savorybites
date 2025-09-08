from django import template

print("Loading cart_filters template tags...")  # Debug statement

register = template.Library()

@register.filter
def in_cart(menu_item_id, cart_item_ids):
    """Check if menu_item_id is in cart_item_ids
    
    Args:
        menu_item_id: The ID of the menu item to check
        cart_item_ids: Can be either a comma-separated string or a list of item IDs
    """
    if not cart_item_ids:
        return False
        
    # If it's a string, split by comma
    if isinstance(cart_item_ids, str):
        return str(menu_item_id) in cart_item_ids.split(',')
    # If it's already a list or other iterable
    else:
        return str(menu_item_id) in (str(item_id) for item_id in cart_item_ids)
