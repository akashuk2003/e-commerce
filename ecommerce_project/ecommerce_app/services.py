from .models import Cart, CartItem, Product

def add_to_cart(user, product_id, quantity=1):
    cart, _ = Cart.objects.get_or_create(user=user)
    product = Product.objects.get(pk=product_id)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
    if not created:
        item.quantity += quantity
        item.save()
    return cart