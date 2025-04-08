from rest_framework import generics
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import Item
from .serializers import ItemSerializer

class ItemListCreate(generics.ListCreateAPIView):
    """
    Retrieve a list of items or create a new item.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

    @extend_schema(
        summary="List all items",
        description="Retrieve a list of all available items in the database.",
        responses={200: ItemSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new item",
        request=ItemSerializer,
        responses={201: ItemSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
