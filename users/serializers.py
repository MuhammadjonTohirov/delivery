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

    def validate(self, attrs):
        # self.username_field should be 'email' due to CustomUser.USERNAME_FIELD
        
        email_attr_key = self.username_field
        input_email = attrs.get(email_attr_key)

        if input_email:
            try:
                # Find the user via case-insensitive email lookup
                # User is already defined as get_user_model() at the top of this file
                user_obj = User.objects.get(email__iexact=input_email)
                # Update attrs with the correctly cased email from the database
                attrs[email_attr_key] = user_obj.email
            except User.DoesNotExist:
                # If no user is found even with a case-insensitive search,
                # the subsequent call to super().validate() will fail and raise
                # an AuthenticationFailed exception, which is the desired behavior.
                pass

        # Call the original validation logic from DRF Simple JWT.
        # This will perform the actual authentication using the (potentially corrected) email.
        data = super().validate(attrs)

        # The get_token method (defined above) will be called by the parent class's logic
        # if authentication is successful, to add custom claims to the token.
        return data


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
            self.create_customer_profile(user, customer_profile_data)
        elif user.role == 'DRIVER' and driver_profile_data is not None:
            self.create_driver_profile(user, driver_profile_data)
        elif user.role == 'RESTAURANT' and restaurant_profile_data is not None:
            self.create_restaurant_profile(user, restaurant_profile_data)
        
        return user
    
    def create_customer_profile(self, user, customer_profile_data):
        if not hasattr(user, 'customer_profile'):
            CustomerProfile.objects.create(user=user, **customer_profile_data)
        else:
            user.customer_profile.__dict__.update(**customer_profile_data)
            user.customer_profile.save()
            
    def create_driver_profile(self, user, driver_profile_data):
        if not hasattr(user, 'driver_profile'):
            DriverProfile.objects.create(user=user, **driver_profile_data)
        else:
            user.driver_profile.__dict__.update(**driver_profile_data)
            user.driver_profile.save()
            
    def create_restaurant_profile(self, user, restaurant_profile_data):
        if not hasattr(user, 'restaurant_profile'):
            RestaurantProfile.objects.create(user=user, **restaurant_profile_data)
        else:
            user.restaurant_profile.__dict__.update(**restaurant_profile_data)
            user.restaurant_profile.save()


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "New passwords do not match."})
        return data
