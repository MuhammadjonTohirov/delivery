from django.db import models
from django.conf import settings
from core.models import TimeStampedModel
from restaurants.models import Restaurant, MenuItem
from decimal import Decimal


class Cart(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
    
    # Cart totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Applied discounts
    applied_coupon = models.ForeignKey('promotions.Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    loyalty_points_used = models.PositiveIntegerField(default=0)
    
    # Delivery details
    delivery_address = models.ForeignKey('geography.Address', on_delete=models.SET_NULL, null=True, blank=True)
    delivery_instructions = models.TextField(blank=True)
    
    # Scheduling
    scheduled_for = models.DateTimeField(null=True, blank=True)
    
    # Cart state
    is_active = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_modified']
    
    def __str__(self):
        return f"Cart for {self.user.full_name} - {self.restaurant.name if self.restaurant else 'Empty'}"
    
    def calculate_totals(self):
        """Recalculate all cart totals"""
        items = self.items.all()
        
        # Calculate subtotal
        self.subtotal = sum(item.total_price for item in items)
        
        # Calculate tax (simplified - 8% tax rate)
        tax_rate = Decimal('0.08')
        self.tax_amount = self.subtotal * tax_rate
        
        # Apply discounts
        self.discount_amount = Decimal('0')
        if self.applied_coupon and self.applied_coupon.is_valid:
            self.discount_amount += self.applied_coupon.calculate_discount(self.subtotal)
        
        # Apply loyalty points discount
        if self.loyalty_points_used > 0:
            try:
                loyalty_account = self.user.loyalty_account
                points_value = self.loyalty_points_used * loyalty_account.program.points_redemption_value
                self.discount_amount += points_value
            except:
                self.loyalty_points_used = 0
        
        # Calculate delivery fee (if address is set)
        self.delivery_fee = Decimal('0')
        if self.delivery_address and self.restaurant:
            try:
                # Get delivery zone for the address
                zone = self.delivery_address.delivery_zone
                if zone:
                    # Calculate distance (simplified)
                    distance = 5.0  # Placeholder - calculate actual distance
                    self.delivery_fee = zone.calculate_delivery_fee(distance, self.subtotal)
                else:
                    self.delivery_fee = Decimal('5.00')  # Default delivery fee
            except:
                self.delivery_fee = Decimal('5.00')
        
        # Calculate final total
        self.total = self.subtotal + self.tax_amount + self.delivery_fee - self.discount_amount
        self.total = max(self.total, Decimal('0'))  # Ensure total is not negative
        
        self.save()
        return self.total
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()
        self.restaurant = None
        self.applied_coupon = None
        self.loyalty_points_used = 0
        self.calculate_totals()
    
    def item_count(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Item customizations
    special_instructions = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('cart', 'menu_item')
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} in {self.cart.user.full_name}'s cart"
    
    def save(self, *args, **kwargs):
        self.unit_price = self.menu_item.price
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        
        # Update cart totals when item changes
        self.cart.calculate_totals()


class CartItemCustomization(TimeStampedModel):
    """For menu item add-ons and modifications"""
    cart_item = models.ForeignKey(CartItem, on_delete=models.CASCADE, related_name='customizations')
    customization = models.ForeignKey('MenuItemCustomization', on_delete=models.CASCADE)
    selected_options = models.JSONField(default=list)  # Selected option IDs
    additional_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Customization for {self.cart_item.menu_item.name}"


class MenuItemCustomization(TimeStampedModel):
    """Define customization options for menu items"""
    CUSTOMIZATION_TYPE_CHOICES = (
        ('SINGLE_SELECT', 'Single Select'),
        ('MULTI_SELECT', 'Multiple Select'),
        ('TEXT_INPUT', 'Text Input'),
        ('QUANTITY', 'Quantity Selection'),
    )
    
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='customizations')
    name = models.CharField(max_length=100)  # "Size", "Toppings", "Spice Level"
    description = models.TextField(blank=True)
    type = models.CharField(max_length=15, choices=CUSTOMIZATION_TYPE_CHOICES)
    
    is_required = models.BooleanField(default=False)
    min_selections = models.PositiveIntegerField(default=0)
    max_selections = models.PositiveIntegerField(null=True, blank=True)
    
    # Display order
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.menu_item.name} - {self.name}"


class CustomizationOption(TimeStampedModel):
    """Individual options for customizations"""
    customization = models.ForeignKey(MenuItemCustomization, on_delete=models.CASCADE, related_name='options')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    additional_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    is_available = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Display order
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        price_str = f" (+${self.additional_price})" if self.additional_price > 0 else ""
        return f"{self.name}{price_str}"


class SavedCart(TimeStampedModel):
    """For saving carts for later (favorites/wishlist)"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_carts')
    name = models.CharField(max_length=100)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    
    # Saved cart data
    cart_data = models.JSONField()  # Serialized cart items and customizations
    
    def __str__(self):
        return f"Saved cart: {self.name} from {self.restaurant.name}"


class CartSession(TimeStampedModel):
    """For anonymous users' cart sessions"""
    session_key = models.CharField(max_length=40, unique=True)
    cart_data = models.JSONField(default=dict)
    
    def __str__(self):
        return f"Anonymous cart session: {self.session_key}"


class CustomerFavorite(TimeStampedModel):
    """Customer's favorite restaurants and menu items"""
    FAVORITE_TYPE_CHOICES = (
        ('RESTAURANT', 'Restaurant'),
        ('MENU_ITEM', 'Menu Item'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    type = models.CharField(max_length=15, choices=FAVORITE_TYPE_CHOICES)
    
    # Favorited objects
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    order_count = models.PositiveIntegerField(default=0)  # How many times ordered
    
    class Meta:
        unique_together = [
            ('user', 'restaurant'),
            ('user', 'menu_item'),
        ]
    
    def __str__(self):
        if self.type == 'RESTAURANT':
            return f"{self.user.full_name} favorites {self.restaurant.name}"
        else:
            return f"{self.user.full_name} favorites {self.menu_item.name}"


class RecentOrder(TimeStampedModel):
    """Track recent orders for easy reordering"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recent_orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    
    # Simplified order data for quick access
    order_summary = models.JSONField()  # Items, total, etc.
    
    class Meta:
        unique_together = ('user', 'order')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Recent order for {self.user.full_name} from {self.restaurant.name}"


class QuickReorder(TimeStampedModel):
    """Saved combinations for quick reordering"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quick_reorders')
    name = models.CharField(max_length=100)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    
    # Order combination
    items_data = models.JSONField()  # Menu items and customizations
    
    # Usage tracking
    last_used = models.DateTimeField(null=True, blank=True)
    use_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"Quick reorder: {self.name} from {self.restaurant.name}"
