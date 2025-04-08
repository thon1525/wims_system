from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .views import CategoryListCreateView
from rest_framework.routers import DefaultRouter
from .views import SupplierViewSet,ProductViewSet,WarehouseViewSet,WarehouseLocationListCreateView, WarehouseLocationDetailView,StockTransactionsViewSet,CategoryDetailView,CustomerListCreateView, CustomerDetailView,CustomerAccountViewSet,OrderViewSet
from django.conf import settings
from django.conf.urls.static import static

from .views import admin_dashboard, get_user_info, ProtectedResourceView, CustomTokenObtainPairView, CustomTokenVerifyView, LogoutView,WarehouseStockPlacementViewSet,WarehouseStockAuditListCreateView, WarehouseStockAuditDetailView,UserAPIView
# Home route
def home(request):
    return JsonResponse({"message": "Welcome to the API Home", "status": "success"})


router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet)  # API Endpoint: /api/suppliers/
router.register(r'products', ProductViewSet, basename='product')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
# router.register(r'warehouse-locations', WarehouseLocationViewSet)
router.register(r'stock-placements', WarehouseStockPlacementViewSet, basename='stock-placement')
router.register(r'stock-transactions', StockTransactionsViewSet, basename='stock-transactions')
router.register(r'customer-accounts', CustomerAccountViewSet)
router.register(r'orders', OrderViewSet)
urlpatterns = [
    # Admin Panel
    path("admin/", admin.site.urls),
    path('api/', include(router.urls)),
    path('api/customers/', CustomerListCreateView.as_view(), name='customer-list-create'),
    path('api/customers/<int:customer_id>/', CustomerDetailView.as_view(), name='customer-detail'),
    path('api/stock-audits/', WarehouseStockAuditListCreateView.as_view(), name='stock_audit_list_create'),
    path('api/stock-audits/<int:pk>/', WarehouseStockAuditDetailView.as_view(), name='stock_audit_detail'),
    path('api/warehouse-locations/', WarehouseLocationListCreateView.as_view(), name='warehouse-location-list-create'),
    path('api/warehouse-locations/<int:id>/', WarehouseLocationDetailView.as_view(), name='warehouse-location-detail'),
    path('api/categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('api/categories/<int:id>/', CategoryDetailView.as_view(), name='category-detail'), 
    # Authentication Routes (JWT)
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/user/", UserAPIView.as_view(), name="user_data"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", CustomTokenVerifyView.as_view(), name="token_verify"),
    path("api/logout/", LogoutView.as_view(), name="auth_logout"),
    # Protected API Endpoints
    path("api/protected-resource/", ProtectedResourceView.as_view(), name="protected_resource"),
    path("api/user/", get_user_info, name="get_user"),
    path("api/admin-dashboard/", admin_dashboard, name="admin_dashboard"),

    # API Documentation (Swagger & ReDoc)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)