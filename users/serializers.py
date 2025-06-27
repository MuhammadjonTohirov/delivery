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
        token['is_restaurant_owner'] = user.is_restaurant_owner()
        token['is_driver'] = user.is_driver()
        token['is_admin'] = user.is_admin_user()

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
    user_type = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'full_name', 'avatar', 'user_type', 'is_active',
                  'date_joined', 'customer_profile', 'driver_profile', 'restaurant_profile']
        read_only_fields = ['id', 'date_joined', 'is_active']
    
    def get_user_type(self, obj) -> dict:
        """Get user type information"""
        return {
            'is_customer': obj.is_customer(),
            'is_driver': obj.is_driver(),
            'is_restaurant_owner': obj.is_restaurant_owner(),
            'is_admin': obj.is_admin_user()
        }
class CustomerSerializer(serializers.ModelSerializer):
    customer_profile = CustomerProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'full_name', 'avatar', 'customer_profile']
        
    def update(self, instance, validated_data):
        # Update the instance with the validated data
        instance.email = validated_data.get('email', instance.email)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.avatar = validated_data.get('avatar', instance.avatar)

        # Update the nested fields (e.g. customer_profile, driver_profile, restaurant_profile)
        if 'customer_profile' in validated_data:
            if hasattr(instance, 'customer_profile'):
                instance.customer_profile.__dict__.update(validated_data['customer_profile'])
                instance.customer_profile.save()
        if 'driver_profile' in validated_data:
            if hasattr(instance, 'driver_profile'):
                instance.driver_profile.__dict__.update(validated_data['driver_profile'])
                instance.driver_profile.save()
        if 'restaurant_profile' in validated_data:
            if hasattr(instance, 'restaurant_profile'):
                instance.restaurant_profile.__dict__.update(validated_data['restaurant_profile'])
                instance.restaurant_profile.save()

        instance.save()
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    create_driver_profile = serializers.BooleanField(required=False, default=False, write_only=True)
    create_restaurant_profile = serializers.BooleanField(required=False, default=False, write_only=True)
    
    # Profile fields based on role
    customer_profile = CustomerProfileSerializer(required=False)
    driver_profile = DriverProfileSerializer(required=False)
    restaurant_profile = RestaurantProfileSerializer(required=False)
    
    def to_internal_value(self, data):
        # Handle JSON string profile data from frontend
        import json
        
        # Convert JSON strings to dictionaries for profile data
        for profile_field in ['customer_profile', 'driver_profile', 'restaurant_profile']:
            if profile_field in data and isinstance(data[profile_field], str):
                try:
                    data[profile_field] = json.loads(data[profile_field])
                except json.JSONDecodeError:
                    pass  # Keep as string, will be handled by validation
        
        return super().to_internal_value(data)
    
    class Meta:
        model = User
        fields = ['email', 'phone', 'full_name', 'avatar', 'password', 'password_confirm',
                 'customer_profile', 'driver_profile', 'restaurant_profile']
    
    def validate(self, data):
        # Validate passwords match
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        
        # Set default profile data if needed
        if 'customer_profile' not in data:
            data['customer_profile'] = {}
        if data.get('create_driver_profile') and 'driver_profile' not in data:
            data['driver_profile'] = {}
        if data.get('create_restaurant_profile') and 'restaurant_profile' not in data:
            data['restaurant_profile'] = {}
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        # Remove profile data and password confirmation from validated_data
        customer_profile_data = validated_data.pop('customer_profile', None)
        driver_profile_data = validated_data.pop('driver_profile', None)
        restaurant_profile_data = validated_data.pop('restaurant_profile', None)
        create_driver_profile = validated_data.pop('create_driver_profile', False)
        create_restaurant_profile = validated_data.pop('create_restaurant_profile', False)
        validated_data.pop('password_confirm')
        
        # Create user
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create customer profile (all users are customers)
        self.create_customer_profile(user, customer_profile_data or {})
        
        # Create additional profiles if requested
        if create_driver_profile:
            self.create_driver_profile(user, driver_profile_data or {})
        if create_restaurant_profile:
            self.create_restaurant_profile(user, restaurant_profile_data or {})
        
        return user
    
    def to_representation(self, instance):
        """Use UserSerializer for output representation"""
        return UserSerializer(instance, context=self.context).data
    
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
            # Ensure required fields have defaults
            if 'business_name' not in restaurant_profile_data:
                restaurant_profile_data['business_name'] = f"{user.full_name}'s Restaurant"
            if 'business_address' not in restaurant_profile_data:
                restaurant_profile_data['business_address'] = "Please update your business address"
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


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True, help_text="Refresh token to blacklist")


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, help_text="Email address for password reset")
    
    def validate_email(self, value):
        try:
            User.objects.get(email__iexact=value)
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            pass
        return value.lower()
