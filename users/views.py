from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import CustomerProfile, DriverProfile, RestaurantProfile
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    PasswordChangeSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer
)
from .permissions import IsOwnerOrAdmin, IsCustomer, IsDriver, IsRestaurantOwner, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    View to obtain token pair with custom claims.
    """
    serializer_class = CustomTokenObtainPairSerializer
    tags = ['Authentication & User Management']
    
    @extend_schema(
        summary="Login to obtain JWT token",
        description="Login endpoint that returns access and refresh tokens",
        responses={200: {"example": {"access": "token", "refresh": "token"}}},
        tags=['Authentication & User Management']
    )
    def post(self, request, *args, **kwargs):
        result = super().post(request, *args, **kwargs)
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
        return  result


class LogoutView(APIView):
    """
    View to blacklist the refresh token, effectively logging out the user.
    """
    permission_classes = [IsAuthenticated]
    tags = ['Authentication & User Management']
    
    @extend_schema(
        summary="Logout and invalidate refresh token",
        description="Blacklists the refresh token to prevent further use",
        request=LogoutSerializer,
        responses={
            205: {
                "description": "Successfully logged out"
            },
            400: {
                "description": "Invalid refresh token or missing token",
                "examples": {
                    "invalid_token": {
                        "summary": "Invalid Token",
                        "value": {"error": "Invalid refresh token"}
                    }
                }
            }
        },
        tags=['Authentication & User Management']
    )
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationView(generics.CreateAPIView):
    """
    View to register a new user.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    tags = ['Authentication & User Management']
    
    @extend_schema(
        summary="Register a new user",
        description="""
        Create a new user account with role-specific profile data.
        
        **Avatar Upload:**
        - Optional profile picture upload
        - Supported formats: JPG, PNG, GIF
        - Maximum file size: 5MB
        - Use multipart/form-data when uploading avatar
        
        **Role-specific profiles:**
        - CUSTOMER: Optional default address and location
        - DRIVER: Vehicle type and license number
        - RESTAURANT: Business name, address, and registration number (required)
        
        **Example with avatar (multipart/form-data):**
        ```
        Content-Type: multipart/form-data
        
        email: user@example.com
        full_name: John Doe
        password: securepass123
        password_confirm: securepass123
        role: CUSTOMER
        avatar: [image file]
        customer_profile: {"default_address": "123 Main St"}
        ```
        
        **Example without avatar (JSON):**
        ```json
        {
          "email": "user@example.com",
          "full_name": "John Doe",
          "password": "securepass123",
          "password_confirm": "securepass123",
          "role": "CUSTOMER",
          "customer_profile": {"default_address": "123 Main St"}
        }
        ```
        """,
        request=UserRegistrationSerializer,
        responses={
            201: UserSerializer,
            400: {
                "description": "Validation errors",
                "examples": {
                    "validation_error": {
                        "summary": "Validation Error Example",
                        "value": {
                            "email": ["This field is required."],
                            "password_confirm": ["Passwords do not match."],
                            "restaurant_profile": ["Restaurant profile is required for restaurant users."]
                        }
                    }
                }
            }
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    View to retrieve or update the authenticated user's profile.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_object(self):
        return self.request.user
    
    @extend_schema(
        summary="Get user profile",
        description="Retrieve the authenticated user's profile information",
        responses={200: UserSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update user profile",
        description="""
        Update the authenticated user's profile information.
        
        **Avatar Upload:**
        - Use multipart/form-data when updating avatar
        - Supported formats: JPG, PNG, GIF
        - Maximum file size: 5MB
        - Previous avatar will be replaced if new one is uploaded
        
        **Example with avatar (multipart/form-data):**
        ```
        Content-Type: multipart/form-data
        
        full_name: Updated Name
        avatar: [new image file]
        ```
        """,
        request=UserSerializer,
        responses={200: UserSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        summary="Partially update user profile",
        description="""
        Partially update the authenticated user's profile information.
        
        **Avatar Upload:**
        - Use multipart/form-data when updating avatar
        - Supported formats: JPG, PNG, GIF
        - Maximum file size: 5MB
        - Previous avatar will be replaced if new one is uploaded
        - Send null or empty to remove existing avatar
        
        **Example with avatar (multipart/form-data):**
        ```
        Content-Type: multipart/form-data
        
        full_name: Updated Name
        avatar: [new image file]
        ```
        """,
        request=UserSerializer,
        responses={200: UserSerializer}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class PasswordChangeView(APIView):
    """
    View to change a user's password.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Change password",
        description="Change the authenticated user's password",
        request=PasswordChangeSerializer,
        responses={
            200: {
                "description": "Password changed successfully",
                "examples": {
                    "success": {
                        "summary": "Success Response",
                        "value": {"message": "Password changed successfully"}
                    }
                }
            },
            400: {
                "description": "Validation errors or incorrect current password",
                "examples": {
                    "validation_error": {
                        "summary": "Validation Error",
                        "value": {
                            "new_password_confirm": ["New passwords do not match."]
                        }
                    },
                    "incorrect_password": {
                        "summary": "Incorrect Current Password",
                        "value": {"error": "Current password is incorrect"}
                    }
                }
            }
        }
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.validated_data['current_password']):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
            return Response({"error": "Current password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerListView(generics.ListAPIView):
    """
    View to list all customers (Admin only).
    """
    queryset = User.objects.all()  # All users are customers
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @extend_schema(
        summary="List all customers",
        description="Returns a list of all customers (Admin only)",
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class DriverListView(generics.ListAPIView):
    """
    View to list all drivers (Admin only).
    """
    queryset = User.objects.filter(driver_profile__isnull=False).distinct()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @extend_schema(
        summary="List all drivers",
        description="Returns a list of all drivers (Admin only)",
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class RestaurantOwnerListView(generics.ListAPIView):
    """
    View to list all restaurant owners (Admin only).
    """
    queryset = User.objects.filter(restaurant__isnull=False).distinct()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @extend_schema(
        summary="List all restaurant owners",
        description="Returns a list of all restaurant owners (Admin only)",
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)