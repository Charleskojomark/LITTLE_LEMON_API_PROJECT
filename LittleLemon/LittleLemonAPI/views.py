from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from .models import MenuItem, Cart, Order, OrderItem, Category
from .serializers import MenuItemSerializer,CategorySerializer, ManagerSerializer, CartSerializer, OrderItemSerializer, ManagerOrderSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator, EmptyPage

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def menu_items(request):
    if request.method == 'GET':
        items = MenuItem.objects.select_related('category').all()
        category_name = request.query_params.get('category')
        to_price = request.query_params.get('to_price')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering')
        perpage = request.query_params.get('perpage', default=2)
        page = request.query_params.get('page', default=1)
        if category_name:
            items = items.filter(category__title=category_name)
        if to_price:
            items = items.filter(price__lte=to_price)
        if search:
            items = items.filter(title__icontains=search)
        if ordering:
            ordering_fields = ordering.split(',')
            items = items.order_by(*ordering_fields)

        paginator = Paginator(items, per_page=perpage)
        try:
            items = paginator.page(number=page)
        except EmptyPage:
            items = []
        serialized = MenuItemSerializer(items, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)
    elif request.method == 'POST' and (request.user.is_staff or request.user.groups.filter(name='Manager').exists()):
        serialized = MenuItemSerializer(data=request.data)
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(serialized.data, status=status.HTTP_201_CREATED)
    elif request.method == 'POST' and not (request.user.is_staff or request.user.groups.filter(name='Manager').exists()):
        return Response("Unauthorized",status=status.HTTP_403_FORBIDDEN)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def categories(request):
    if request.method == 'GET':
        items = Category.objects.all()
        serialized = CategorySerializer(items, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)
    elif request.method == 'POST' and (request.user.is_staff or request.user.groups.filter(name='Manager').exists()):
        serialized = CategorySerializer(data=request.data)
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(serialized.data, status=status.HTTP_201_CREATED)
    elif request.method == 'POST' and not (request.user.is_staff or request.user.groups.filter(name='Manager').exists()):
        return Response("Unauthorized",status=status.HTTP_403_FORBIDDEN)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def single_item(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'GET':
        serializer = MenuItemSerializer(item)
        return Response(serializer.data)
    elif request.user.is_staff or request.user.groups.filter(name='Manager').exists():
        if request.method == 'PUT':
            serializer = MenuItemSerializer(item, data=request.data)
        elif request.method == 'PATCH':
            serializer = MenuItemSerializer(item, data=request.data, partial=True)
        elif request.method == 'DELETE':
            item.delete()
            return Response(status=status.HTTP_200_OK)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_403_FORBIDDEN)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def managers(request):
    if request.user.is_staff or request.user.groups.filter(name='Manager').exists():
        if request.method == 'GET':
            manager = User.objects.filter(groups__name='Manager')
            serialized = ManagerSerializer(manager, many=True)
            return Response(serialized.data, status=status.HTTP_200_OK)
        elif request.method == 'POST':
            username = request.data.get('username')
            if username:
                user = get_object_or_404(User, username=username)
                managers = Group.objects.get(name='Manager')
                managers.user_set.add(user)
                return Response(f"{username} added to managers",status=status.HTTP_201_CREATED)
            return Response("Provide a valid username",status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def manager_delete(request, pk):
    if request.user.is_staff or request.user.groups.filter(name='Manager').exists():
        username = request.data.get('username')
        user = get_object_or_404(User, pk=pk, username=username)
        managers = Group.objects.get(name='Manager')
        managers.user_set.remove(user)
        return Response(f"{username} removed from managers",status=status.HTTP_200_OK)
    else:
        return Response("You are not authorized",status=status.HTTP_403_FORBIDDEN)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def delivery(request):
    if request.user.is_staff or request.user.groups.filter(name='Manager').exists():
        if request.method == 'GET':
            delivery = User.objects.filter(groups__name='Delivery')
            serialized = ManagerSerializer(delivery, many=True)
            return Response(serialized.data, status=status.HTTP_200_OK)
        elif request.method == 'POST':
            username = request.data.get('username')
            if username:
                user = get_object_or_404(User, username=username)
                delivery_group = Group.objects.get(name='Delivery')
                delivery_group.user_set.add(user)
                return Response(f"{username} has been added to delivery crew",status=status.HTTP_201_CREATED)
            return Response('Provide a valid username',status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delivery_delete(request, pk):
    if request.user.is_staff or request.user.groups.filter(name='Manager').exists():
        user = get_object_or_404(User, pk=pk)
        delivery_group = Group.objects.get(name='Delivery')
        delivery_group.user_set.remove(user)
        return Response(f"user with id {pk} has been removed from delivery group",status=status.HTTP_200_OK)
    else:
        return Response("Not authorized",status=status.HTTP_403_FORBIDDEN)

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_menu_items(request):
    if request.method == 'GET':
        cart_items = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        try:
            menuitem_id = request.data.get('menuitem')
            quantity = request.data.get('quantity')
            if menuitem_id is None or quantity is None:
                return Response({'error': 'menuitem and quantity are required'}, status=status.HTTP_400_BAD_REQUEST)
            menuitem = MenuItem.objects.get(pk=menuitem_id)
            cart_item = Cart(user=request.user, menuitem=menuitem, quantity=quantity)
            cart_item.save()
            serializer = CartSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except TypeError:
            return Response({'created successfully'}, status=status.HTTP_201_CREATED)
    elif request.method == 'DELETE':
        Cart.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def orders(request):
    if request.method == 'GET':
        if request.user.groups.filter(name='Manager').exists():
            orders = Order.objects.all()
            orders = Order.objects.filter(user=request.user)
            to_total = request.query_params.get('to_total')
            search = request.query_params.get('search')
            ordering = request.query_params.get('ordering')
            perpage = request.query_params.get('perpage', default=2)
            page = request.query_params.get('page', default=1)
            if to_total:
                orders = orders.filter(total__lte=to_total)
            if search:
                orders = orders.filter(status=search)
            if ordering:
                ordering_fields = ordering.split(',')
                orders = orders.order_by(*ordering_fields)

            paginator = Paginator(orders, per_page=perpage)
            try:
                orders = paginator.page(number=page)
            except EmptyPage:
                orders = []
                serializer = ManagerOrderSerializer(orders, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        try:
            serializer = ManagerOrderSerializer(data=request.data)
            user = request.user
            cart_items = user.cart_set.all()
            if not cart_items:
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
            total_price = sum(item.menuitem.price * item.quantity for item in cart_items)
            order = Order.objects.create(user=user, total=total_price)
            for cart_item in cart_items:
                OrderItem.objects.create(order=order, menuitem=cart_item.menuitem, quantity=cart_item.quantity)
            cart_items.delete()
            serializer = ManagerOrderSerializer(order)
            return Response({'Order created successfully'},serializer.data, status=status.HTTP_201_CREATED)
        except TypeError:
            return Response({'created successfully'})

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.user != order.user and not request.user.groups.filter(name='Manager').exists():
        return Response({'error': 'You are not authorized to access this order'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        order_items = OrderItem.objects.filter(order=order)
        serializer = OrderItemSerializer(order_items, many=True)
        return Response(serializer.data)
    elif request.method in ['PUT', 'PATCH']:
        order = get_object_or_404(Order, pk=pk)
        if not request.user.groups.filter(name='Manager').exists():
            return Response({'error': 'You are not authorized to update this order'}, status=status.HTTP_403_FORBIDDEN)
        
        serialized = ManagerOrderSerializer(order, partial=True, data=request.data)
        if serialized.is_valid():
            serialized.save()
        return Response(serialized.data)
    elif request.method == 'DELETE':
        if request.user.groups.filter(name='Manager').exists():
            order.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)
 