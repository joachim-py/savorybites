from django.urls import path
from savorybites import views

urlpatterns = [
    path('', views.index, name="index"),
    path('reservation/', views.book_reservation, name="book-reservation"),
    path('contact/', views.contact_us, name="contact-us"),
    path('add-to-cart/', views.add_to_cart, name="add-to-cart"),
    path('cart/remove/<int:cart_item_id>/', views.remove_from_cart, name="remove-from-cart"),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/update/<int:cart_item_id>/', views.update_cart_quantity, name="update-cart-quantity"),
    path('cart/', views.view_cart, name="cart"),
    path('checkout/', views.checkout, name="checkout"),
    path('payment/<int:order_id>/', views.payment, name="payment"),
    path('orders/', views.orders, name="orders"),
    path('menu/', views.menu, name="menu"),
    path('menu/category/<str:category>/', views.menu, name="menu-category"),
    path('contact/', views.contact_us, name="contact-us"),
    path('reservations/', views.reservations, name="reservations"),
    path('reviews/', views.reviews, name="reviews"),
    path('gallery/', views.gallery, name="gallery"),
    path('profile/', views.profile, name="profile"),
    path('verify/', views.payment_callback, name='payment_callback'),
]
