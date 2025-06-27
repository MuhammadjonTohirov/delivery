from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import ApplicationSettings
from .serializers import ApplicationSettingsSerializer, PublicSettingsSerializer


@extend_schema(
    summary="Get public application settings",
    description="Get public application settings that don't require authentication",
    responses={200: PublicSettingsSerializer}
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def public_settings(request):
    """
    Get public application settings (no authentication required)
    """
    settings = ApplicationSettings.get_settings()
    serializer = PublicSettingsSerializer(settings)
    return Response(serializer.data)


@extend_schema(
    summary="Get application settings",
    description="Get all application settings (admin only)",
    responses={200: ApplicationSettingsSerializer}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def get_settings(request):
    """
    Get application settings (admin only)
    """
    settings = ApplicationSettings.get_settings()
    serializer = ApplicationSettingsSerializer(settings)
    return Response(serializer.data)


@extend_schema(
    summary="Update application settings",
    description="Update application settings (admin only)",
    request=ApplicationSettingsSerializer,
    responses={200: ApplicationSettingsSerializer}
)
@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def update_settings(request):
    """
    Update application settings (admin only)
    """
    settings = ApplicationSettings.get_settings()
    serializer = ApplicationSettingsSerializer(
        settings, 
        data=request.data, 
        partial=request.method == 'PATCH'
    )
    
    if serializer.is_valid():
        serializer.save()
        
        # Refresh cache after settings update
        from .startup import refresh_settings_cache
        refresh_settings_cache()
        
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)