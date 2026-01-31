from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, UserSerializer
from rest_framework import status
from .models import Product, Category, Cart, CartItem, Order, OrderItem
from .serializers import ProductSerializer, CategorySerializer, CartSerializer, CartItemSerializer


@api_view(['GET'])
def get_products(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_product(request, pk=None):
    try:
        product = Product.objects.get(id=pk)
        serializer = ProductSerializer(product, context={'request': request})
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)


@api_view(['GET'])
def get_categories(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    product_id = request.data.get('product_id')
    
    if not product_id:
        return Response({'error': 'product_id is required'}, status=400)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        item.quantity += 1
        item.save()
    
    return Response({
        'message': 'Product added to cart',
        'cart': CartSerializer(cart).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_cart_quantity(request):
    item_id = request.data.get('item_id')
    quantity = request.data.get('quantity')

    if not item_id or quantity is None:
        return Response({'error': 'item_id and quantity are required'}, status=400)
    
    try:
        quantity = int(quantity)
        if quantity < 1:
            return Response({'error': 'Quantity must be at least 1'}, status=400)
        
        item = CartItem.objects.get(id=item_id, cart__user=request.user)
        item.quantity = quantity
        item.save()
        
        return Response(CartItemSerializer(item).data)
    
    except ValueError:
        return Response({'error': 'Invalid quantity value'}, status=400)
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found or not yours'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request):
    item_id = request.data.get('item_id')
    
    if not item_id:
        return Response({'error': 'item_id is required'}, status=400)

    deleted_count, _ = CartItem.objects.filter(
        id=item_id,
        cart__user=request.user
    ).delete()
    
    if deleted_count == 0:
        return Response({'error': 'Item not found or not in your cart'}, status=404)
    
    return Response({'message': 'Item removed from cart'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    try:
        data = request.data
        address = data.get('address')
        phone = data.get('phone')
        payment_method = data.get('payment_method', 'COD')

        if not address:
            return Response({'error': 'Delivery address is required'}, status=400)
        
        if not phone or not phone.isdigit() or len(phone) != 10:
            return Response({'error': 'Valid 10-digit phone number is required'}, status=400)

        cart, _ = Cart.objects.get_or_create(user=request.user)

        if not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=400)

        # Using the property you defined → very clean
        total = cart.total

        # Create order
        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            # Agar Order model mein address/phone/payment_method field add karoge to yahan save kar sakte ho
            # address=address,
            # phone=phone,
            # payment_method=payment_method,
        )

        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,  # snapshot of price at order time
            )

        # Clear the cart
        cart.items.all().delete()

        return Response({
            'message': 'Order created successfully',
            'order_id': order.id,
            'total_amount': str(total),
        }, status=201)

    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "message": "User Created Successfully",
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


