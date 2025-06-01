from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from core.models import TimeStampedModel
import uuid


class Cart(TimeStampedModel):
    """
    Shopping cart for customers
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, null=True, blank=True)
    
    # Cart metadata
    session_key = models.CharField(max_length=40, null=True, blank=True)  # For anonymous users
    is_active = models.BooleanField(default=True)
    
    # Delivery details
    delivery_address = models.TextField(null=True, blank=True)
    delivery_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_instructions = models.TextField(null=True, blank=True)
    
    # Timing
    requested_delivery_time = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
            models.Index(fields=['restaurant']),
        ]
    
    def __str__(self):
        return f"Cart for {self.user.full_name if self.user else 'Anonymous'}"
    
    @property
    def total_items(self):
        """Get total number of items in cart"""
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def subtotal(self):
        """Calculate cart subtotal"""
        total = 0
        for item in self.items.all():
            total += item.subtotal
        return total
    
    @property
    def estimated_delivery_fee(self):
        """Calculate estimated delivery fee"""
        if not self.delivery_lat or not self.delivery_lng or not self.restaurant:
            return 0
        
        from geography.utils import calculate_distance, calculate_delivery_fee
        
        if self.restaurant.location_lat and self.restaurant.location_lng:
            distance = calculate_distance(
                float(self.restaurant.location_lat), float(self.restaurant.location_lng),
                float(self.delivery_lat), float(self.delivery_lng)
            )
            return calculate_delivery_fee(distance)
        
        return 2.50  # Default delivery fee
    
    @property
    def total(self):
        """Calculate total including delivery fee"""
        return self.subtotal + self.estimated_delivery_fee
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()
        self.restaurant = None
        self.save()
    
    def add_item(self, menu_item, quantity=1, special_instructions=''):
        """Add or update item in cart"""
        # If cart has items from different restaurant, clear it
        if self.restaurant and self.restaurant != menu_item.restaurant:
            self.clear()
        
        # Set restaurant if not set
        if not self.restaurant:
            self.restaurant = menu_item.restaurant
            self.save()
        
        # Get or create cart item
        cart_item, created = self.items.get_or_create(
            menu_item=menu_item,
            defaults={
                'quantity': quantity,
                'unit_price': menu_item.price,
                'special_instructions': special_instructions
            }
        )
        
        if not created:
            cart_item.quantity += quantity
            if special_instructions:
                cart_item.special_instructions = special_instructions
            cart_item.save()
        
        return cart_item
    
    def remove_item(self, menu_item):
        """Remove item from cart"""
        self.items.filter(menu_item=menu_item).delete()
    
    def update_item_quantity(self, menu_item, quantity):
        """Update quantity of an item in cart"""
        if quantity <= 0:
            self.remove_item(menu_item)
            return None
        
        try:
            cart_item = self.items.get(menu_item=menu_item)
            cart_item.quantity = quantity
            cart_item.save()
            return cart_item
        except CartItem.DoesNotExist:
            return None


class CartItem(TimeStampedModel):
    """
    Individual item in a shopping cart
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey('restaurants.MenuItem', on_delete=models.CASCADE)
    
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    special_instructions = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('cart', 'menu_item')
        indexes = [
            models.Index(fields=['cart']),
            models.Index(fields=['menu_item']),
        ]
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} in {self.cart}"
    
    @property
    def subtotal(self):
        """Calculate subtotal for this cart item"""
        return self.quantity * self.unit_price
    
    def save(self, *args, **kwargs):
        # Set unit price from menu item if not set
        if not self.unit_price:
            self.unit_price = self.menu_item.price
        super().save(*args, **kwargs)


class SavedCart(TimeStampedModel):
    """
    Saved carts for later or favorite orders
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_carts')
    name = models.CharField(max_length=100)
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE)
    
    # Cart data stored as JSON
    cart_data = models.JSONField()
    
    # Metadata
    is_favorite = models.BooleanField(default=False)
    times_reordered = models.PositiveIntegerField(default=0)
    last_ordered = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'name')
        indexes = [
            models.Index(fields=['user', 'is_favorite']),
            models.Index(fields=['restaurant']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.name}"
    
    def restore_to_cart(self):
        """Restore this saved cart to user's active cart"""
        cart, created = Cart.objects.get_or_create(user=self.user)
        
        # Clear current cart
        cart.clear()
        
        # Set restaurant
        cart.restaurant = self.restaurant
        cart.save()
        
        # Add items from saved cart
        for item_data in self.cart_data.get('items', []):
            try:
                menu_item = self.restaurant.menu_items.get(id=item_data['menu_item_id'])
                cart.add_item(
                    menu_item=menu_item,
                    quantity=item_data['quantity'],
                    special_instructions=item_data.get('special_instructions', '')
                )
            except Exception:
                continue  # Skip items that no longer exist
        
        return cart
    
    @classmethod
    def create_from_cart(cls, user, cart, name):
        """Create a saved cart from current cart"""
        cart_data = {
            'items': [
                {
                    'menu_item_id': str(item.menu_item.id),
                    'menu_item_name': item.menu_item.name,
                    'quantity': item.quantity,
                    'unit_price': str(item.unit_price),
                    'special_instructions': item.special_instructions
                }
                for item in cart.items.all()
            ],
            'restaurant_id': str(cart.restaurant.id),
            'restaurant_name': cart.restaurant.name,
            'subtotal': str(cart.subtotal),
            'created_from_cart_at': cart.created_at.isoformat()
        }
        
        saved_cart = cls.objects.create(
            user=user,
            name=name,
            restaurant=cart.restaurant,
            cart_data=cart_data
        )
        
        return saved_cart


class CartPromotion(models.Model):
    """
    Applied promotions/discounts to cart
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='applied_promotions')
    promotion = models.ForeignKey('promotions.Promotion', on_delete=models.CASCADE)
    
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    applied_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('cart', 'promotion')
    
    def __str__(self):
        return f"Promotion applied to {self.cart}"


class CartAbandonment(models.Model):
    """
    Track abandoned carts for analytics and remarketing
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE)
    
    # Cart snapshot
    items_count = models.PositiveIntegerField()
    cart_value = models.DecimalField(max_digits=10, decimal_places=2)
    cart_data = models.JSONField()
    
    # Abandonment details
    abandoned_at = models.DateTimeField()
    abandonment_stage = models.CharField(max_length=20, choices=[
        ('BROWSING', 'Browsing Menu'),
        ('CART', 'Items in Cart'),
        ('CHECKOUT', 'At Checkout'),
        ('PAYMENT', 'At Payment'),
    ])
    
    # Recovery tracking
    recovered = models.BooleanField(default=False)
    recovered_at = models.DateTimeField(null=True, blank=True)
    recovery_order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'abandoned_at']),
            models.Index(fields=['restaurant', 'abandoned_at']),
            models.Index(fields=['recovered']),
        ]
    
    def __str__(self):
        user_identifier = self.user.full_name if self.user else f"Anonymous ({self.session_key})"
        return f"Abandoned cart by {user_identifier} - ${self.cart_value}"
