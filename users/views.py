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
    CustomTokenObtainPairSerializer
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
    
    @extend_schema(
        summary="Login to obtain JWT token",
        description="Login endpoint that returns access and refresh tokens",
        responses={200: {"example": {"access": "token", "refresh": "token"}}}
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
    
    @extend_schema(
        summary="Logout and invalidate refresh token",
        description="Blacklists the refresh token to prevent further use",
        responses={205: None}
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
    
    @extend_schema(
        summary="Register a new user",
        description="Create a new user account with role-specific profile data",
        responses={201: UserSerializer}
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
        description="Update the authenticated user's profile information",
        responses={200: UserSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        summary="Partially update user profile",
        description="Partially update the authenticated user's profile information",
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
        responses={200: {"example": {"message": "Password changed successfully"}}}
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
    queryset = User.objects.filter(role='CUSTOMER')
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
    queryset = User.objects.filter(role='DRIVER')
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
    queryset = User.objects.filter(role='RESTAURANT')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @extend_schema(
        summary="List all restaurant owners",
        description="Returns a list of all restaurant owners (Admin only)",
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)