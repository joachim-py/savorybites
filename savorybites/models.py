import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Menu(models.Model):
    
    class CategoryChoices(models.TextChoices):
        STARTER = 'ST', 'Starter'
        MAIN_COURSE = 'MC', 'Main Course'
        DESSERT = 'DE', 'Dessert'
        DRINKS = 'DR', 'Drinks'
        SNACKS = 'SN', 'Snacks'
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_images/')
    category = models.CharField(max_length=50, choices=CategoryChoices.choices, default=CategoryChoices.MAIN_COURSE)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    class Meta:
         verbose_name_plural = "Menu"

class Special(models.Model):
    menu_item = models.ForeignKey('Menu', on_delete=models.CASCADE, related_name='specials')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Special: {self.menu_item.name} - {self.discount_percentage}% off"

    class Meta:
        verbose_name_plural = "Specials"

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    menu_item = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

    @property
    def subtotal(self):
        return self.menu_item.price * self.quantity

    @subtotal.setter
    def subtotal(self, value):
        self._subtotal = value
        return f"{self.quantity}x {self.menu_item.name}"

    class Meta:
        verbose_name_plural = "Cart Items"

class Order(models.Model):
    order_id = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    customer_address = models.TextField()
    delivery_option = models.CharField(max_length=20, choices=[
        ('dine_in', 'Dine In'),
        ('takeaway', 'Takeaway'),
        ('delivery', 'Delivery')
    ], default='dine_in')
    special_instructions = models.TextField(blank=True)
    cart_items = models.ManyToManyField(CartItem, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed')
    ], default='pending')
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order_id} - {self.customer_name}"

    class Meta:
        verbose_name_plural = "Orders"

    def calculate_total(self):
        self.total_price = sum(item.menu_item.price * item.quantity for item in self.cart_items.all())
        self.save()

class Contact(models.Model):
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    contact_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contact from {self.customer_name} on {self.contact_date}"
    
class Reservation(models.Model):
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15)
    number_of_guests = models.PositiveIntegerField()
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    special_requests = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Reservation by {self.customer_name} on {self.reservation_date}"

class Review(models.Model):
    class RatingChoices(models.TextChoices):
        ONE_STAR = '1', '1 Star'
        TWO_STARS = '2', '2 Stars'
        THREE_STARS = '3', '3 Stars'
        FOUR_STARS = '4', '4 Stars'
        FIVE_STARS = '5', '5 Stars'
    
    customer_name = models.CharField(max_length=100)
    customer_occupation = models.CharField(max_length=100)
    image = models.ImageField(upload_to='review_images/', null=True, blank=True)
    rating = models.CharField(max_length=15, choices=RatingChoices.choices, default=RatingChoices.THREE_STARS)
    comment = models.TextField()
    review_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.customer_name} with rating {self.rating}"
    
    def get_initials(self):
        """
        Returns initials for avatar generation:
        - If two or more words: first letter of first and last word.
        - If one word: first two letters.
        """
        parts = self.customer_name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        elif len(parts) == 1:
            return parts[0][:2].upper()
        return ""
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Delivery(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    delivery_date = models.DateTimeField()
    delivery_status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], default='scheduled')
    delivery_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Delivery for Order {self.order.order_id}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"
    class RatingChoices(models.TextChoices):
        ONE_STAR = '1', '1 Star'
        TWO_STARS = '2', '2 Stars'
        THREE_STARS = '3', '3 Stars'
        FOUR_STARS = '4', '4 Stars'
        FIVE_STARS = '5', '5 Stars'
    
    customer_name = models.CharField(max_length=100)
    customer_occupation = models.CharField(max_length=100)
    image = models.ImageField(upload_to='review_images/', null=True, blank=True)
    rating = models.CharField(max_length=15, choices=RatingChoices.choices, default=RatingChoices.THREE_STARS)
    comment = models.TextField()
    review_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.customer_name} with rating {self.rating}"
    
    def get_initials(self):
        """
        Returns initials for avatar generation:
        - If two or more words: first letter of first and last word.
        - If one word: first two letters.
        """
        parts = self.customer_name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        elif len(parts) == 1:
            return parts[0][:2].upper()
        return ""
    
class Gallery(models.Model):
    image = models.ImageField(upload_to='gallery_images/')
    description = models.TextField(blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Gallery Image {self.id}"
    
    class Meta:
        verbose_name_plural = "Gallery"

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=[
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('cash', 'Cash on Delivery')
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending')
    reference = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    def __str__(self):
        return f"Payment for Order {self.order.order_id} of amount {self.amount}"

