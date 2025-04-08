import datetime
import traceback
from wims.authentication import CookieJWTAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes , authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenVerifyView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from django.conf import settings
from rest_framework import generics
from .serializers import CategorySerializer,ProductSerializer,WarehouseSerializer,WarehouseLocationSerializer,WarehouseStockPlacement,OrderSerializer
from .models import Category,Product,StockTransactions,Customer,CustomerAccount,Order, OrderItem, POSTransaction
from rest_framework import viewsets
from .serializers import SupplierSerializer,WarehouseLocation,WarehouseStockPlacementSerializer,StockTransactionsSerializer,WarehouseStockAuditSerializer,CustomerSerializer,CustomerAccountSerializer
from rest_framework.decorators import action
from .models import Supplier,Warehouse,WarehouseStockAudit
from rest_framework.exceptions import ValidationError
import pandas as pd
User = get_user_model()
import logging

logger = logging.getLogger(__name__)
# 🔹 Public API Route (No Authentication Required)
@api_view(["GET"])
def hello_world(request):
    """Public route for API testing."""
    return Response({"message": "Hello, World!"})

# 🔹 Protected Admin Dashboard (Requires Authentication)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    """Protected route for admin users."""
    return Response({"message": "Welcome, Admin!"})

# 🔹 JWT Token Verification (Custom Response)
class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return Response({"detail": "Token is valid"}, status=status.HTTP_200_OK)
        return response


class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'id'  # Explicitly set to 'id' (default is 'pk')    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Only use the cookie, no need for request.data
            refresh_token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])

            if not refresh_token:
                logger.warning("No refresh token found in cookies")
                # Still proceed to clear cookies even if no token
                response = Response({"message": "Logged out, no refresh token provided"}, status=200)
            else:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info(f"Refresh token blacklisted for user {request.user.id}")
                response = Response({"message": "Successfully logged out"}, status=200)

            # Clear cookies regardless
            response.delete_cookie(
                settings.SIMPLE_JWT["AUTH_COOKIE"],
                path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
                samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
            )
            response.delete_cookie(
                settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"],
                path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
                samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
            )

            return response
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({"error": str(e)}, status=400)
# 🔹 Protected API Resource (Requires Authentication)
class ProtectedResourceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Returns a message with authenticated user info."""
        return Response({"message": "This is a protected resource!", "user": str(request.user)})

# 🔹 Custom JWT Authentication (Stores Token in Cookies)
class MyProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "You are authenticated"})
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            access_token = response.data.get("access")
            refresh_token = response.data.get("refresh")

            if access_token and refresh_token:
                secure_cookie = not settings.DEBUG  # True in production

                response.set_cookie(
                    key=settings.SIMPLE_JWT["AUTH_COOKIE"],
                    value=access_token,
                    httponly=True,
                    secure=secure_cookie,
                    samesite="Lax",  # Works with same-origin (proxied) requests
                    expires=datetime.datetime.now() + settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
                    path="/",
                    domain="localhost",  # Match the frontend's domain
                )
                response.set_cookie(
                    key=settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"],
                    value=refresh_token,
                    httponly=True,
                    secure=secure_cookie,
                    samesite="Lax",
                    expires=datetime.datetime.now() + settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
                    path="/api/token/refresh/",
                    domain="localhost",
                )

                del response.data["access"]
                del response.data["refresh"]
                print("🔹 Get Authenticated User Information", access_token)

            response.data = {"message": "Login successful"}
        else:
            response.data = {"message": "Invalid credentials"}

        return response
    
@api_view(["GET"])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    print("🔹 Get Authenticated User Information")
    print("🔹 Request Cookies:", request.COOKIES)  # Add this line
    """
    Retrieves authenticated user details using JWT from HttpOnly cookies.
    """
    try:
        user = request.user  
        if not user or not user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        print("⚠️ Error fetching user info:", e)
        traceback.print_exc()
        return Response({"error": "Internal Server Error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by("name_company")
    serializer_class = SupplierSerializer   

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # Enable file uploads

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def choices(self, request):
        return Response({
            'unit_types': [{'value': value, 'label': label} for value, label in Product.UNIT_CHOICES]
        })

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='import-excel')
    def import_excel(self, request):
        if 'file' not in request.FILES:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        excel_file = request.FILES['file']
        
        try:
            # Read Excel file with pandas
            df = pd.read_excel(excel_file)
            if df.empty:
                return Response({"error": "Excel file is empty"}, status=status.HTTP_400_BAD_REQUEST)

            # Convert to list of dictionaries
            products_data = df.to_dict('records')
            created_products = []
            errors = []

            for index, product_data in enumerate(products_data):
                try:
                    # Handle category and supplier
                    category, _ = Category.objects.get_or_create(
                        name_category=str(product_data.get('Category', 'Uncategorized') or 'Uncategorized')
                    )
                    supplier, _ = Supplier.objects.get_or_create(
                        name_company=str(product_data.get('Supplier', 'N/A') or 'N/A')
                    )

                    # Handle Price: Remove '$' and convert to float
                    price_str = str(product_data.get('Price', '0') or '0')
                    price = float(price_str.replace('$', '').strip()) if price_str else 0.0

                    # Handle Weight: Convert "N/A" to 0.0
                    weight_str = str(product_data.get('Weight', '0') or '0')
                    weight = 0.0 if weight_str == 'N/A' else float(weight_str)

                    # Build product data
                    product_dict = {
                        
                        'name': str(product_data.get('Name', '') or ''),
                        'sku': str(product_data.get('SKU', '') or ''),
                        'barcode': str(product_data.get('Barcode', '') or ''),
                        'price': price,
                        'weight': weight,
                        'quantity': int(product_data.get('Quantity', 0) or 0),
                        'category': category.pk,
                        'supplier': supplier.pk,
                        'is_active': str(product_data.get('Status', 'Active')).lower() == 'active'
                    }

                    # Validate and save
                    serializer = ProductSerializer(data=product_dict, context={'request': request})
                    if serializer.is_valid():
                        serializer.save()
                        created_products.append(serializer.data)
                    else:
                        errors.append({
                            'row': index + 2,
                            'data': product_dict,
                            'errors': serializer.errors
                        })
                except (ValueError, TypeError) as e:
                    errors.append({
                        'row': index + 2,
                        'data': product_data,
                        'error': f"Invalid data format: {str(e)}"
                    })
                except Exception as e:
                    errors.append({
                        'row': index + 2,
                        'data': product_data,
                        'error': str(e)
                    })

            response_data = {
                'created': len(created_products),
                'errors': errors if errors else None
            }
            status_code = status.HTTP_201_CREATED if not errors else status.HTTP_207_MULTI_STATUS
            return Response(response_data, status=status_code)

        except pd.errors.EmptyDataError:
            return Response({"error": "Excel file is empty or invalid"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to process Excel file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Handle POST request to create a new warehouse."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """Handle PUT/PATCH request to update an existing warehouse."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        status_code = status.HTTP_206_PARTIAL_CONTENT if partial else status.HTTP_200_OK
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status_code, headers=headers)

    def destroy(self, request, *args, **kwargs):
        """Handle DELETE request to remove a warehouse."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    


class WarehouseLocationListCreateView(generics.ListCreateAPIView):
    queryset = WarehouseLocation.objects.all()
    serializer_class = WarehouseLocationSerializer

class WarehouseLocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WarehouseLocation.objects.all()
    serializer_class = WarehouseLocationSerializer
    lookup_field = 'id'

class WarehouseStockPlacementViewSet(viewsets.ModelViewSet):
    queryset = WarehouseStockPlacement.objects.all()
    serializer_class = WarehouseStockPlacementSerializer
    def get_queryset(self):
        """
        Optionally filter the queryset by product_id if provided in query params
        """
        queryset = WarehouseStockPlacement.objects.all()
        product_id = self.request.query_params.get('product_id', None)
        if product_id is not None:
            queryset = queryset.filter(product__product_id=product_id)
        return queryset
        
    @transaction.atomic
    def perform_create(self, serializer):
        """
        Create a new placement and update product quantity
        """
        # Get the product before saving the placement
        product_id = self.request.data.get('product')
        product = get_object_or_404(Product, product_id=product_id)
        transaction_type = self.request.data.get('transaction_type', 'INBOUND')
        if transaction_type not in dict(StockTransactions.TRANSACTION_TYPES):
            raise serializers.ValidationError(f"Invalid transaction type: {transaction_type}")
        
        # Get the quantity from the request data
        placement_quantity = int(self.request.data.get('quantity', 0))
        
        # Check if there's enough quantity in product
        if transaction_type == 'INBOUND':
            # For INBOUND, we might want to ADD to product quantity instead of subtract
            # Adjust this logic based on your business requirements
            pass  # No validation needed for adding stock
        elif transaction_type == 'OUTBOUND':
            # For OUTBOUND, check if there's enough stock
            if product.quantity < placement_quantity:
                raise serializers.ValidationError(
                    f"Insufficient stock. Available: {product.quantity}, Requested: {placement_quantity}"
                )
        
        # Save the placement
        instance = serializer.save()
        if transaction_type == 'INBOUND':
            product.quantity += placement_quantity  # Add stock for inbound
            logger.info(f"INBOUND: Adding {placement_quantity} to product {product.product_id}")
        elif transaction_type == 'OUTBOUND':
            product.quantity -= placement_quantity  # Remove stock for outbound
            logger.info(f"OUTBOUND: Removing {placement_quantity} from product {product.product_id}")
        # Update product quantity
        product.quantity -= placement_quantity
        product.save()

        StockTransactions.objects.create(
            stock=instance,
            transaction_type=transaction_type,
            quantity=placement_quantity
        )
        logger.info(f"Created {transaction_type} transaction for {placement_quantity} units")

    @transaction.atomic
    def perform_update(self, serializer):
        """
        Update existing placement and adjust product quantity accordingly
        """
        instance = self.get_object()
        old_quantity = instance.quantity
        product = instance.product
        
        # Save the updated placement
        instance = serializer.save()
        new_quantity = instance.quantity
        
        # Calculate the difference and adjust product quantity
        quantity_diff = new_quantity - old_quantity
        if quantity_diff != 0:
            if product.quantity < quantity_diff:
                raise serializers.ValidationError(
                    f"Insufficient stock. Available: {product.quantity}, Requested increase: {quantity_diff}"
                )
            product.quantity -= quantity_diff
            product.save()

    def perform_destroy(self, instance):
        """
        Delete placement and add quantity back to product
        """
        product = instance.product
        placement_quantity = instance.quantity

        logger.info(f"Deleting placement {instance.stock_id} for product {product.product_id} with quantity {placement_quantity}")
        logger.info(f"Current product quantity: {product.quantity}")

        try:
            with transaction.atomic():
                # Lock the product row to prevent concurrent updates
                product = Product.objects.select_for_update().get(product_id=product.product_id)

                # Verify quantity is positive before updating
                if placement_quantity < 0:
                    logger.error(f"Invalid placement quantity: {placement_quantity}")
                    raise ValueError("Cannot add back negative quantity to product")

                # Update product quantity
                product.quantity += placement_quantity
                logger.info(f"New product quantity will be: {product.quantity}")

                # Save the product
                product.save()
                logger.info(f"Product {product.product_id} saved with new quantity: {product.quantity}")

                # Delete the placement
                instance.delete()
                logger.info(f"Placement {instance.stock_id} deleted successfully")

        except Exception as e:
            logger.error(f"Error in perform_destroy: {str(e)}")
            raise
    
class StockTransactionsViewSet(viewsets.ModelViewSet):
    queryset = StockTransactions.objects.all()
    serializer_class = StockTransactionsSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Add business logic, e.g., update stock quantity
        instance = serializer.save()
        stock = instance.stock
        if instance.transaction_type == 'INBOUND':
            stock.quantity += instance.quantity
        elif instance.transaction_type == 'OUTBOUND':
            stock.quantity -= instance.quantity
        stock.save()    



class WarehouseStockAuditListCreateView(generics.ListCreateAPIView):
    queryset = WarehouseStockAudit.objects.all()
    serializer_class = WarehouseStockAuditSerializer
    permission_classes = [IsAuthenticated]

class WarehouseStockAuditDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WarehouseStockAudit.objects.all()
    serializer_class = WarehouseStockAuditSerializer
    permission_classes = [IsAuthenticated]
    

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Extract tokens from response data
        access_token = response.data['access']
        refresh_token = response.data['refresh']
        
        # Check if "remember me" is in the request
        remember_me = request.data.get('remember_me', False)
        
        # Set cookie expiration based on "remember me"
        access_max_age = 60 * 60 * 24  # 1 day default
        refresh_max_age = 60 * 60 * 24 * 7  # 7 days default
        if remember_me:
            access_max_age = 60 * 60 * 24 * 30  # 30 days for "remember me"
            refresh_max_age = 60 * 60 * 24 * 60  # 60 days for "remember me"
        
        # Set cookies in the response
        response.set_cookie(
            key='access_token',
            value=access_token,
            max_age=access_max_age,
            httponly=True,
            secure=True,  # Use True in production (HTTPS)
            samesite='Lax'
        )
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            max_age=refresh_max_age,
            httponly=True,
            secure=True,  # Use True in production (HTTPS)
            samesite='Lax'
        )
        
        # Remove tokens from response body (optional, since they're in cookies)
        response.data = {"message": "Login successful"}
        return response


class UserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"username": request.user.username, "message": "Protected data"})        
    
class CustomerListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    lookup_field = 'customer_id'

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
    

class CustomerAccountViewSet(viewsets.ModelViewSet):
    queryset = CustomerAccount.objects.all()
    serializer_class = CustomerAccountSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        customer_id = request.data.get('customer')
        if customer_id and CustomerAccount.objects.filter(customer_id=customer_id).exists():
            raise ValidationError({"customer": "A customer account for this customer already exists."})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related('customer').prefetch_related('items__product', 'items__warehouse', 'items__location')
    serializer_class = OrderSerializer
    http_method_names = ['get', 'post', 'put', 'delete']

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            logger.error(f"Validation error: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Save the order with items
        order = serializer.save()

        total_price = 0
        for item in order.items.all():  # Items are already created by the serializer
            product = item.product
            quantity = item.quantity
            warehouse = item.warehouse
            location = item.location

           # Check stock availability
            stock = (WarehouseStockPlacement.objects
                     .select_related('product')
                     .filter(product=product, warehouse=warehouse, location=location)
                     .first())
            logger.info(f"Checking stock for {product.name} at {warehouse.name}")
            if not stock or stock.quantity - stock.reserved_quantity < quantity:
                logger.warning(f"Insufficient stock for {product.name} at {warehouse.name}")
                return Response(
                    {"error": f"Insufficient stock for {product.name}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

          #  Reserve stock
            stock.reserved_quantity += quantity
            stock.save()

            # Create POS transaction
            pos_transaction = POSTransaction.objects.create(
                order=order,
                customer=order.customer,
                product=product,
                barcode=product.barcode,
                quantity=quantity,
                pos_terminal_id=order.pos_terminal_id or "POS_DEFAULT",
                status='Verified'
            )

            # Update the OrderItem with the POS transaction
            item.pos_transaction = pos_transaction
            item.save()

            total_price += item.price

        # Update order
        order.total_price = total_price
        order.status = 'Reserved'
        order.reserved_at = timezone.now()
        order.save()

        logger.info(f"Order {order.order_id} created successfully")
        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)