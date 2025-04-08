from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from rest_framework.exceptions import NotFound
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom error handler for Django REST Framework.
    Returns JSON responses for all errors with a consistent structure.
    """
    # Handle Django's 404 error separately
    if isinstance(exc, Http404) or isinstance(exc, NotFound):
        return Response(
            {
                "success": False,
                "error": "Not Found",
                "message": "The requested resource was not found.",
                "detail": "Please check the URL or contact support if the issue persists.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # Let DRF handle other exceptions first
    response = exception_handler(exc, context)

    # If DRF did not handle the exception, log and return a 500 error as JSON.
    if response is None:
        logger.error(f"Unhandled error: {exc}")
        return Response(
            {
                "success": False,
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later.",
                "detail": str(exc),  # For production, you might want to hide the error detail.
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Customize responses for known errors
    if response.status_code == 400:
        return Response(
            {
                "success": False,
                "error": "Bad Request",
                "message": "Invalid request data. Please review and try again.",
                "detail": response.data,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if response.status_code == 401:
        return Response(
            {
                "success": False,
                "error": "Unauthorized",
                "message": "Authentication credentials were not provided or are invalid.",
                "detail": response.data,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if response.status_code == 403:
        return Response(
            {
                "success": False,
                "error": "Forbidden",
                "message": "You do not have permission to perform this action.",
                "detail": "Please check your user role or contact support if you believe this is an error.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # For any other responses, simply return them as-is
    return response
