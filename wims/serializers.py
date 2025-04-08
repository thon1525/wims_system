from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Category,Product
from .models import Supplier,Warehouse,WarehouseLocation,WarehouseStockPlacement,StockTransactions,WarehouseStockAudit,Customer,CustomerAccount,Order, OrderItem, POSTransaction

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()  # ✅ Ensures proper name handling

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'is_superuser', 'is_staff']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username  # ✅ Falls back to username if no full name

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'  # Include all fields

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"  # Include all fields in the API     

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name_category', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name_company', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'product_id', 'name', 'category', 'category_name', 'supplier', 'supplier_name',
            'sku', 'barcode', 'price', 'weight', 'quantity', 'image', 'image_url','unit_type',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['product_id', 'created_at', 'updated_at', 'category_name', 'supplier_name']
    def get_unit_type_choices(self):
        return [{'value': value, 'label': label} for value, label in Product.UNIT_CHOICES]    

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None
    
class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['warehouse_id', 'name', 'address']  # Fields to expose in API
        read_only_fields = ['warehouse_id']  # Auto-generated field

    def validate_name(self, value):
        """Ensure name is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty.")
        return value

    def validate_address(self, value):
        """Ensure address is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Address cannot be empty.")
        return value
    
class WarehouseLocationSerializer(serializers.ModelSerializer):
    warehouse = serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.all())

    class Meta:
        model = WarehouseLocation
        fields = ['id', 'warehouse', 'section_name', 'storage_type', 'capacity_class', 'max_capacity', 'created_at', 'updated_at']


class WarehouseStockPlacementSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    location_section = serializers.CharField(source='location.section_name', read_only=True)
    category_name = serializers.CharField(source='category.name_category', read_only=True)

    class Meta:
        model = WarehouseStockPlacement
        fields = [
            'stock_id', 'warehouse', 'warehouse_name', 'product', 'product_name',
            'location', 'location_section', 'category', 'category_name', 'quantity',
            'weight', 'storage_type', 'batch_number', 'expiry_date', 'last_updated',
            'min_stock_level', 'max_stock_level'
        ]
        read_only_fields = ['stock_id', 'last_updated']        

class StockTransactionsSerializer(serializers.ModelSerializer):
    stock_id = serializers.PrimaryKeyRelatedField(
        queryset=WarehouseStockPlacement.objects.all(),
        source='stock'
    )
    product_name = serializers.CharField(source='stock.product.name', read_only=True)
    warehouse_name = serializers.CharField(source='stock.warehouse.name', read_only=True)

    class Meta:
        model = StockTransactions
        fields = ['transaction_id', 'stock_id', 'transaction_type', 'quantity', 'transaction_date', 'product_name', 'warehouse_name']   


class WarehouseStockAuditSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    location_name = serializers.CharField(source='location.section_name', read_only=True)

    class Meta:
        model = WarehouseStockAudit
        fields = [
            'audit_id', 'warehouse', 'warehouse_name', 'product', 'product_name',
            'location', 'location_name', 'recorded_quantity', 'audit_date'
        ]
        read_only_fields = ['audit_id', 'audit_date']

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'customer_id', 'full_name', 'first_name', 'last_name', 'email',
            'profile_image', 'phone', 'address', 'account_status',
            'created_date', 'last_updated'
        ]        

class CustomerAccountSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    password = serializers.CharField(write_only=True)  # Raw password input

    class Meta:
        model = CustomerAccount
        fields = ['account_id', 'customer', 'customer_name', 'username', 'password', 'account_created_date']
        read_only_fields = ['account_id', 'account_created_date']

    def create(self, validated_data):
        raw_password = validated_data.pop('password')
        account = CustomerAccount(**validated_data)
        account.set_password(raw_password)
        account.save()
        return account

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'password':
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance
    

class POSTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSTransaction
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    warehouse = serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.all())
    location = serializers.PrimaryKeyRelatedField(queryset=WarehouseLocation.objects.all())
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['order_item_id', 'order', 'product', 'product_name', 'warehouse', 'location', 'quantity', 'price', 'pos_transaction']
        read_only_fields = ['order', 'price', 'order_item_id', 'pos_transaction']  # These are set by the backend

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['order_id', 'customer', 'order_date', 'status', 'total_price', 'pos_processed', 'pos_terminal_id', 'reserved_at', 'fulfilled_at', 'items']
        read_only_fields = ['order_id', 'order_date', 'status', 'total_price', 'reserved_at', 'fulfilled_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        
        # Manually create OrderItems since we handle price and order in the view
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                warehouse=item_data['warehouse'],
                location=item_data['location'],
                quantity=item_data['quantity'],
                price=item_data['product'].price * item_data['quantity']  # Calculate price here
            )
            print(f"OrderItem created: {item_data['product'].quantity} with quantity {item_data['quantity']}")
        return order