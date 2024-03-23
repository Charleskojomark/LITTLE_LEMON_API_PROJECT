from rest_framework import serializers
from .models import Category, MenuItem, Cart,Order,OrderItem
from django.contrib.auth.models import User, Group
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','slug', 'title']

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    class Meta:
        model = MenuItem
        fields = ['id', 'title','price','featured','category','category_id']
        
class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        
class CartSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField(method_name='get_price')
    unit_price = serializers.SerializerMethodField(method_name='get_unit_price')
    class Meta:
        model = Cart
        fields = ['id', 'user', 'menuitem','unit_price','quantity','price']
    
    def get_unit_price(self, cart_instance):
        menuitem = cart_instance.menuitem
        return menuitem.price if menuitem else None
    
    def get_price(self, cart_instance):
        return cart_instance.menuitem.price * cart_instance.quantity


class OrderItemSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField(method_name='get_price')
    unit_price = serializers.SerializerMethodField(method_name='get_unit_price')
    
    class Meta:
        model = OrderItem
        fields = ['order', 'menuitem', 'quantity', 'price', 'unit_price']
    def get_unit_price(self, cart_instance):
        menuitem = cart_instance.menuitem
        return menuitem.price if menuitem else None
    
    def get_price(self, cart_instance):
        return cart_instance.menuitem.price * cart_instance.quantity

class ManagerOrderSerializer(serializers.ModelSerializer):

    orderitem = OrderItemSerializer(many=True, read_only=True, source='order')

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew',
                  'status', 'date', 'total', 'orderitem']

        
# class OrderItemSerializer(serializers.ModelSerializer):
#     price = serializers.SerializerMethodField(method_name='get_price')
#     unit_price = serializers.SerializerMethodField(method_name='get_unit_price')
#     delivery_crew = serializers.CharField(source='order.delivery_crew')
#     status = serializers.CharField(source='order.status')
#     # menuitem = serializers.CharField(source='menuitem.title')
#     class Meta:
#         model = OrderItem
#         fields = ['id', 'menuitem', 'quantity','unit_price','price','delivery_crew','status']
        
#     def get_unit_price(self, cart_instance):
#         menuitem = cart_instance.menuitem
#         return menuitem.price if menuitem else None
    
#     def get_price(self, cart_instance):
#         return cart_instance.menuitem.price * cart_instance.quantity


# class ManagerOrderSerializer(serializers.ModelSerializer):
#     order_items = OrderItemSerializer(many=True, read_only=True)

#     class Meta:
#         model = Order
#         fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date','order_items']