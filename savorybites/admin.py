from django.contrib import admin
from savorybites import models

# Register your models here.
@admin.register(models.Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category']
    search_fields = ['name', 'price', 'category']
    
@admin.register(models.Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['image', 'upload_date']
    search_fields = ['upload_date']
    
@admin.register(models.Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'customer_occupation', 'rating', 'review_date']
    search_fields = ['customer_name', 'customer_occupation', 'rating', 'review_date']
@admin.register(models.Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'customer_email', 'number_of_guests', 'reservation_date', 'reservation_time']
    search_fields = ['customer_name', 'customer_email', 'reservation_date', 'reservation_time']
@admin.register(models.Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'customer_email', 'subject', 'contact_date']
    search_fields = ['customer_name', 'customer_email', 'subject', 'contact_date']

