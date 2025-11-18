from django.urls import path
from . import views

urlpatterns = [
    path("", views.store_home, name="store-home"),
    path("product/<slug:slug>/", views.product_detail_page, name="product-detail-page"),
    path("cart/", views.cart_page, name="cart-page"),
    path("wishlist/", views.wishlist_page, name="wishlist-page"),
    path("checkout/", views.checkout_page, name="checkout-page"),
]
