from rest_framework import generics, viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect, render
from .models import Product, Category, Cart, CartItem, Wishlist, Address, Order, OrderItem
from .serializers import (
ProductSerializer, CategorySerializer, CartSerializer, CartItemSerializer,
WishlistSerializer, AddressSerializer, OrderSerializer
)
from django.db import transaction
from ecommerce_app import serializers


class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    pagination_class = None

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


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _get_cart(self, user):
        cart, created = Cart.objects.get_or_create(user=user)
        return cart

    def list(self, request):
        cart = self._get_cart(request.user)
        serializer = CartSerializer(cart)
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
                item.product.stock = max(0, item.product.stock - item.quantity)
                item.product.save(update_fields=['stock'])

            order.total = total
            order.save(update_fields=['total'])
            cart.items.all().delete()

        return Response({'order_id': order.id, 'total': order.total}, status=status.HTTP_201_CREATED)


def store_home(request):
    products = Product.objects.all()
    return render(request, "ecommerce_app/index.html", {"products": products})

def product_detail_page(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, "ecommerce_app/product_detail.html", {"product": product})


def cart_page(request):
    cart = None
    items = []

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            items = cart.items.all()

    return render(request, "ecommerce_app/cart.html", {"cart": cart, "items": items})


def wishlist_page(request):
    wishlist = None
    products = []

    if request.user.is_authenticated:
        wishlist = Wishlist.objects.filter(user=request.user).first()
        if wishlist:
            products = wishlist.products.all()

    return render(request, "ecommerce_app/wishlist.html", {"wishlist": wishlist, "products": products})


def checkout_page(request):
    if not request.user.is_authenticated:
        return redirect("/login/")  # Optional

    addresses = Address.objects.filter(user=request.user)
    return render(request, "ecommerce_app/checkout.html", {"addresses": addresses})
