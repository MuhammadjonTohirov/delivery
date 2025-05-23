from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CustomerProfile, DriverProfile, RestaurantProfile
from django.db import transaction
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['email'] = user.email
        token['full_name'] = user.full_name
        token['role'] = user.role

        return token


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ['default_address', 'default_location_lat', 'default_location_lng']


class DriverProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = ['vehicle_type', 'license_number']


class RestaurantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantProfile
        fields = ['business_name', 'business_address', 'business_registration_number']


class UserSerializer(serializers.ModelSerializer):
    customer_profile = CustomerProfileSerializer(required=False)
    driver_profile = DriverProfileSerializer(required=False)
    restaurant_profile = RestaurantProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'full_name', 'role', 'is_active', 
                  'date_joined', 'customer_profile', 'driver_profile', 'restaurant_profile']
        read_only_fields = ['id', 'date_joined', 'is_active']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    # Profile fields based on role
    customer_profile = CustomerProfileSerializer(required=False)
    driver_profile = DriverProfileSerializer(required=False)
    restaurant_profile = RestaurantProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = ['email', 'phone', 'full_name', 'password', 'password_confirm', 
                 'role', 'customer_profile', 'driver_profile', 'restaurant_profile']
    
    def validate(self, data):
        # Validate passwords match
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        
        # Validate role-specific profile data
        role = data.get('role', 'CUSTOMER')
        
        if role == 'CUSTOMER' and 'customer_profile' not in data:
            data['customer_profile'] = {}
        elif role == 'DRIVER' and 'driver_profile' not in data:
            data['driver_profile'] = {}
        elif role == 'RESTAURANT' and 'restaurant_profile' not in data:
            raise serializers.ValidationError({"restaurant_profile": "Restaurant profile is required for restaurant users."})
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        # Remove profile data and password confirmation from validated_data
        customer_profile_data = validated_data.pop('customer_profile', None)
        driver_profile_data = validated_data.pop('driver_profile', None)
        restaurant_profile_data = validated_data.pop('restaurant_profile', None)
        validated_data.pop('password_confirm')
        
        # Create user
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create appropriate profile based on role
        if user.role == 'CUSTOMER' and customer_profile_data is not None:
            CustomerProfile.objects.create(user=user, **customer_profile_data)
        elif user.role == 'DRIVER' and driver_profile_data is not None:
            DriverProfile.objects.create(user=user, **driver_profile_data)
        elif user.role == 'RESTAURANT' and restaurant_profile_data is not None:
            RestaurantProfile.objects.create(user=user, **restaurant_profile_data)
        
        return user


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "New passwords do not match."})
        return data