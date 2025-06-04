from django.urls import path
from savorybites import views

urlpatterns = [
    path('', views.index, name="index"),
    path('reservation/', views.book_reservation, name="book_reservation"),
    path('contact/', views.contact_us, name="contact_us"),
]