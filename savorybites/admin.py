from django.contrib import admin
from savorybites.models import (
    Menu, Contact, Gallery, Reservation, Review,
    CartItem, Order, Payment, Profile, Special, Delivery
)

# Menu Admin
@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_per_page = 20

# Special Admin
@admin.register(Special)
class SpecialAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'discount_percentage', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('menu_item__name',)
    ordering = ('-start_date',)
    list_per_page = 20

# CartItem Admin
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'menu_item', 'quantity', 'subtotal', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('session_key', 'menu_item__name')
    list_per_page = 20

# Order Admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id', 'customer_name', 'customer_email', 'customer_phone', 
        'delivery_option', 'total_price', 'status', 'payment_status', 
        'order_date'
    )
    list_filter = (
        'status', 'payment_status', 'order_date', 'delivery_option'
    )
    search_fields = (
        'customer_name', 'customer_email', 'customer_phone', 
        'customer_address', 'special_instructions'
    )
    readonly_fields = (
        'order_date', 'total_price'
    )
    
    fieldsets = (
        ('Order Information', {
            'fields': (
                'customer_name', 'customer_email', 'customer_phone',
                'customer_address', 'delivery_option', 'special_instructions',
                'status', 'payment_status', 'order_date'
            )
        }),
        ('Cart Items', {
            'fields': ('cart_items',)
        }),
        ('Financial', {
            'fields': ('total_price',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        # Recalculate total if cart items changed
        if 'cart_items' in form.changed_data:
            obj.calculate_total()
        super().save_model(request, obj, form, change)

# Payment Admin
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order__order_id', 'payment_method', 'amount', 'status', 'reference', 'payment_date')
    list_filter = ('payment_method', 'status', 'payment_date')
    search_fields = ('order__customer_name', 'reference')
    ordering = ('-payment_date',)
    list_per_page = 20
    readonly_fields = ('reference',)
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('order__order_id', 'payment_method', 'amount', 'status', 'reference')
        }),
        ('Financial', {
            'fields': ('payment_date',)
        })
    )

# Profile Admin
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number')
    search_fields = ('user__username', 'phone_number')
    list_per_page = 20

# Gallery Admin
@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('image', 'description', 'upload_date')
    list_filter = ('upload_date',)
    search_fields = ('description',)
    ordering = ('-upload_date',)
    list_per_page = 20

# Review Admin
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'rating', 'review_date', 'get_initials')
    list_filter = ('rating', 'review_date')
    search_fields = ('customer_name', 'comment')
    ordering = ('-review_date',)
    list_per_page = 20

# Reservation Admin
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'customer_email', 'number_of_guests', 'reservation_date', 'reservation_time')
    list_filter = ('reservation_date',)
    search_fields = ('customer_name', 'customer_email')
    ordering = ('-reservation_date',)
    list_per_page = 20

# Contact Admin
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'customer_email', 'subject', 'contact_date')
    search_fields = ('customer_name', 'customer_email', 'subject', 'message')
    ordering = ('-contact_date',)
    list_per_page = 20

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('order__order_id', 'order__customer_address', 'delivery_date', 'delivery_status', 'delivery_person')
    list_filter = ('delivery_date', 'delivery_status')
    search_fields = ('order__customer_name',)
    ordering = ('-delivery_date',)
    list_per_page = 20


