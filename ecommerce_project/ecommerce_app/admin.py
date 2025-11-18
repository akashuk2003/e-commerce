from django.contrib import admin
from .models import (
    Category, Product, ProductImage, Address,
    Cart, CartItem, Wishlist, Order, OrderItem, PaymentRecord
)
from ecommerce_app import serializers

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'stock', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('category',)
    inlines = [ProductImageInline]
    prepopulated_fields = {"slug": ("title",)}

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'is_default')
    search_fields = ('full_name', 'city', 'postal_code')
    list_filter = ('city', 'is_default')

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at', 'subtotal')
    inlines = [CartItemInline]

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user',)
    filter_horizontal = ('products',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product', 'quantity', 'price')
    can_delete = False
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total', 'created_at')
    search_fields = ('user__username', 'id')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]

@admin.register(PaymentRecord)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'order', 'method', 'status', 'amount', 'created_at')
    search_fields = ('payment_id',)
    list_filter = ('method', 'status')






# ecommerce/views.py
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Product, Category, Cart, CartItem, Wishlist, Address, Order, OrderItem
from .serializers import (
    ProductSerializer, CategorySerializer, CartSerializer, CartItemSerializer,
    WishlistSerializer, AddressSerializer, OrderSerializer
)
from django.db import transaction

# Product list & detail
class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # swap with PageNumberPagination in real app

    def get_queryset(self):
        qs = Product.objects.all().prefetch_related('images', 'category')
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category__slug=category)
        return qs

class ProductDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    queryset = Product.objects.all().prefetch_related('images', 'category')


# Cart and wishlist as viewsets
class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _get_cart(self, user):
        cart, created = Cart.objects.get_or_create(user=user)
        return cart

    def list(self, request):
        cart = self._get_cart(request.user)
        serializer = CartSerializer(cart)
        # attach computed subtotal
        data = serializer.data
        data['subtotal'] = cart.subtotal
        return Response(data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        product_id = request.data.get('product_id')
        qty = int(request.data.get('quantity', 1))
        product = get_object_or_404(Product, pk=product_id)
        cart = self._get_cart(request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product,
                                                      defaults={'quantity': qty})
        if not created:
            item.quantity = item.quantity + qty
            item.save()
        return Response({'ok': True, 'subtotal': cart.subtotal})

    @action(detail=False, methods=['post'])
    def update_item(self, request):
        item_id = request.data.get('item_id')
        qty = int(request.data.get('quantity', 1))
        item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
        if qty <= 0:
            item.delete()
        else:
            item.quantity = qty
            item.save()
        return Response({'ok': True, 'subtotal': item.cart.subtotal if hasattr(item, 'cart') else 0})

    @action(detail=False, methods=['post'])
    def remove(self, request):
        item_id = request.data.get('item_id')
        item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
        cart = item.cart
        item.delete()
        return Response({'ok': True, 'subtotal': cart.subtotal})


class WishlistViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _get_wishlist(self, user):
        wishlist, _ = Wishlist.objects.get_or_create(user=user)
        return wishlist

    def list(self, request):
        wishlist = self._get_wishlist(request.user)
        serializer = WishlistSerializer(wishlist)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        pid = request.data.get('product_id')
        product = get_object_or_404(Product, pk=pid)
        wishlist = self._get_wishlist(request.user)
        if product in wishlist.products.all():
            wishlist.products.remove(product)
            return Response({'status': 'removed'})
        else:
            wishlist.products.add(product)
            return Response({'status': 'added'})


class AddressViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CheckoutAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        address_id = request.data.get('address_id')
        address = get_object_or_404(Address, pk=address_id, user=request.user)
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            return Response({'detail': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            order = Order.objects.create(user=request.user, address=address, status='PENDING')
            total = 0
            for item in cart.items.select_related('product'):
                if item.quantity > item.product.stock:
                    raise serializers.ValidationError(f"Not enough stock for {item.product.title}")
                oi = OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                total += oi.subtotal
                # optionally reduce stock
                item.product.stock = max(0, item.product.stock - item.quantity)
                item.product.save(update_fields=['stock'])

            order.total = total
            order.save(update_fields=['total'])
            # clear cart
            cart.items.all().delete()

        return Response({'order_id': order.id, 'total': order.total}, status=status.HTTP_201_CREATED)


# ecommerce/urls.py
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
]


# ecommerce/services.py (utility helpers)
from .models import Cart, CartItem, Product

def add_to_cart(user, product_id, quantity=1):
    cart, _ = Cart.objects.get_or_create(user=user)
    product = Product.objects.get(pk=product_id)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
    if not created:
        item.quantity += quantity
        item.save()
    return cart

