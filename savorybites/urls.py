from django.urls import path
from savorybites import views

urlpatterns = [
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:cart_item_id>/', views.update_cart_quantity, name='update_cart'),
    path('cart/remove/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    path('', views.index, name="index"),
    path('menu/', views.menu, name="menu"),
    path('login/', views.login, name="login"),
    path('signup/', views.signup, name="signup"),
    path('logout/', views.logout, name="logout"),
    path('orders/', views.orders, name="orders"),
    path('reviews/', views.reviews, name="reviews"),
    path('profile/', views.profile, name="profile"),
    path('gallery/', views.gallery, name="gallery"),
    path('profile/', views.profile, name="profile"),
    path('checkout/', views.checkout, name="checkout"),
    path('contact/', views.contact_us, name="contact-us"),
    path('payment/<int:order_id>/', views.payment, name="payment"),
    path('reservations/', views.reservations, name="reservations"),
    path('verify/', views.payment_callback, name='payment_callback'),
    path('reservation/', views.book_reservation, name="book-reservation"),
    path('menu/category/<str:category>/', views.menu, name="menu-category"),
    path('orders/<int:order_id>/details/', views.order_details_json, name='order_details_json'),
]
