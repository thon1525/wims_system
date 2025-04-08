from django.db import models
from django.core.validators import MinValueValidator
from .category_wims import Category
from .supplies_wims import Supplier
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
class Product(models.Model):
    UNIT_CHOICES = [
        ('single', 'Single'),
        ('case', 'Case'),
        ('box', 'Box'),
    ]
        
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Product Name")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", verbose_name="Category")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="products", verbose_name="Supplier")
    sku = models.CharField(max_length=20, unique=True, verbose_name="SKU")
    barcode = models.CharField(max_length=50, unique=True, verbose_name="Barcode")
    unit_type = models.CharField(max_length=10, choices=UNIT_CHOICES, default='single', verbose_name="Unit Type")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Price")
    weight = models.FloatField(default=0, validators=[MinValueValidator(0)], verbose_name="Weight")
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Quantity")
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)  # Update field for image upload
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["name"]

    def __str__(self):
        return self.name
    

class Warehouse(models.Model):
    warehouse_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, null=False, blank=False)  # NOT NULL enforced
    address = models.CharField(max_length=255, null=False, blank=False)  # NOT NULL enforced

    class Meta:
        verbose_name = "Warehouse"
        verbose_name_plural = "Warehouses"
        ordering = ["name"]  # Order alphabetically by name

    def __str__(self):
        return self.name  # Show warehouse name when printed
    


class WarehouseLocation(models.Model):
    STORAGE_TYPES = (
        ('Shelf', 'Shelf'),
        ('Rack', 'Rack'),
        ('Cold Storage', 'Cold Storage'),
    )
    
    CAPACITY_CLASSES = (
        ('Small', 'Small'),
        ('Medium', 'Medium'),
        ('Large', 'Large'),
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='locations'
    )
    section_name = models.CharField(max_length=50)
    storage_type = models.CharField(max_length=50, choices=STORAGE_TYPES)
    capacity_class = models.CharField(max_length=20, choices=CAPACITY_CLASSES)
    max_capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Warehouse Location"
        verbose_name_plural = "Warehouse Locations"
        unique_together = ('warehouse', 'section_name')

    def __str__(self):
        return f"{self.warehouse.name} - {self.section_name}"
    

class WarehouseStockPlacement(models.Model):
    """
    Model to manage stock placement in warehouses.
    """
    STORAGE_TYPE_CHOICES = [
        ('shelf', 'Shelf'),
        ('rack', 'Rack'),
        ('cold_storage', 'Cold Storage'),
        ('pallet', 'Pallet'),
    ]

    stock_id = models.AutoField(primary_key=True)
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='stock_placements',
        verbose_name="Warehouse"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_placements',
        verbose_name="Product"
    )
    location = models.ForeignKey(
        WarehouseLocation,
        on_delete=models.CASCADE,
        related_name='stock_placements',
        verbose_name="Location"
    )
    reserved_quantity = models.IntegerField(  # New field
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Reserved Quantity"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='stock_placements',
        verbose_name="Category"
    )
    quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Quantity"
    )
    weight = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Total Weight"
    )
    storage_type = models.CharField(
        max_length=50,
        choices=STORAGE_TYPE_CHOICES,
        verbose_name="Storage Type"
    )
    batch_number = models.CharField(
        max_length=50,
        verbose_name="Batch Number"
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Expiry Date"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Last Updated"
    )
    min_stock_level = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Minimum Stock Level"
    )
    max_stock_level = models.IntegerField(
        default=1000,
        validators=[MinValueValidator(0)],
        verbose_name="Maximum Stock Level"
    )

    class Meta:
        verbose_name = "Warehouse Stock Placement"
        verbose_name_plural = "Warehouse Stock Placements"
        ordering = ['-last_updated']
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=0),
                name='quantity_non_negative'
            ),
            models.CheckConstraint(
                check=models.Q(weight__gte=0),
                name='weight_non_negative'
            ),
        ]

    def __str__(self):
        return f"{self.product.name} at {self.warehouse.name} - {self.location.section_name}"    
    

class StockTransactions(models.Model):
    TRANSACTION_TYPES = [
        ('INBOUND', 'Inbound'),
        ('OUTBOUND', 'Outbound'),
    ]

    transaction_id = models.AutoField(primary_key=True)
    stock = models.ForeignKey(
        'WarehouseStockPlacement',
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="Stock Placement"
    )
    transaction_type = models.CharField(
        max_length=8,
        choices=TRANSACTION_TYPES,
        verbose_name="Transaction Type"
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Quantity"
    )
    transaction_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Transaction Date"
    )

    class Meta:
        verbose_name = "Stock Transaction"
        verbose_name_plural = "Stock Transactions"
        ordering = ['-transaction_date']

    def __str__(self):
        return f"{self.transaction_type} - {self.stock.product.name} ({self.quantity})"    
    

class WarehouseStockAudit(models.Model):
    audit_id = models.AutoField(primary_key=True)
    warehouse = models.ForeignKey(
        'Warehouse',
        on_delete=models.CASCADE,
        related_name='stock_audits',
        verbose_name="Warehouse"
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='stock_audits',
        verbose_name="Product"
    )
    location = models.ForeignKey(
        'WarehouseLocation',
        on_delete=models.CASCADE,
        related_name='stock_audits',
        verbose_name="Location"
    )
    recorded_quantity = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Recorded Quantity"
    )
    audit_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Audit Date"
    )

    class Meta:
        verbose_name = "Warehouse Stock Audit"
        verbose_name_plural = "Warehouse Stock Audits"
        ordering = ['-audit_date']

    def __str__(self):
        return f"Audit {self.audit_id} - {self.product.name} at {self.warehouse.name}"    
    


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=50, null=False, blank=False)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    profile_image = models.CharField(max_length=225, null=True, blank=True)  # Could be changed to ImageField if storing files
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    account_status = models.CharField(
        max_length=20,
        choices=[('Active', 'Active'), ('Inactive', 'Inactive'), ('Pending', 'Pending')],
        default='Pending'
    )
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = 'customers'    

class CustomerAccount(models.Model):
    account_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='accounts',
        verbose_name="Customer"
    )
    username = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Username"
    )
    password_hash = models.CharField(
        max_length=255,
        verbose_name="Password Hash"
    )
    account_created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Account Created Date"
    )

    class Meta:
        verbose_name = "Customer Account"
        verbose_name_plural = "Customer Accounts"
        ordering = ['-account_created_date']

    def __str__(self):
        return f"{self.username} ({self.customer.name})"       

    def set_password(self, raw_password):
        """Hash and set the password."""
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        """Verify the password against the stored hash."""
        return check_password(raw_password, self.password_hash) 
    

class Order(models.Model):
    STATUS_CHOICES = [
        ('Received', 'Received'),
        ('Processing', 'Processing'),
        ('Reserved', 'Reserved'),
        ('Picked', 'Picked'),
        ('Packed', 'Packed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    order_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey('Customer', on_delete=models.RESTRICT, related_name='orders')
    order_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Received')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pos_processed = models.BooleanField(default=False)
    pos_terminal_id = models.CharField(max_length=50, null=True, blank=True)
    reserved_at = models.DateTimeField(null=True, blank=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-order_date']

    def __str__(self):
        return f"Order {self.order_id} - {self.customer.full_name}"

class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    warehouse = models.ForeignKey('Warehouse', on_delete=models.CASCADE)
    location = models.ForeignKey('WarehouseLocation', on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    pos_transaction = models.ForeignKey('POSTransaction', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.product.name} (Order {self.order.order_id})"

class POSTransaction(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Verified', 'Verified'),
    ]

    pos_transaction_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='pos_transactions')
    customer = models.ForeignKey('Customer', on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    barcode = models.CharField(max_length=50)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    transaction_date = models.DateTimeField(default=timezone.now)
    pos_terminal_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    class Meta:
        verbose_name = "POS Transaction"
        verbose_name_plural = "POS Transactions"
        ordering = ['-transaction_date']

    def __str__(self):
        return f"POS {self.pos_transaction_id} - {self.product.name}"    