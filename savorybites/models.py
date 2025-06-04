from django.db import models
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

# class Order(models.Model):
#     customer_name = models.CharField(max_length=100)
#     customer_email = models.EmailField()
#     menu_item = models.ForeignKey(Menu, on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField()
#     order_date = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Order by {self.customer_name} for {self.menu_item.name}"

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
    
class Gallery(models.Model):
    image = models.ImageField(upload_to='gallery_images/')
    description = models.TextField(blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Gallery Image {self.id}"
    
    class Meta:
        verbose_name_plural = "Gallery"

# class Payment(models.Model):
#     order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
#     payment_date = models.DateTimeField(auto_now_add=True)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     payment_method = models.CharField(max_length=50)

#     def __str__(self):
#         return f"Payment for Order {self.order.id} of amount {self.amount}"

