from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductListAPIView, ProductDetailAPIView, CartViewSet, WishlistViewSet, AddressViewSet, CheckoutAPIView


router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'addresses', AddressViewSet, basename='addresses')


urlpatterns = [
path('products/', ProductListAPIView.as_view(), name='product-list'),
path('products/<slug:slug>/', ProductDetailAPIView.as_view(), name='product-detail'),
path('checkout/', CheckoutAPIView.as_view(), name='checkout'),
path('', include(router.urls)),
path("", views.store_home, name="store-home"),
]