from datetime import datetime
from random import shuffle
from django.shortcuts import render
from django.http import JsonResponse
from savorybites.models import Contact, Gallery, Menu, Reservation, Review
# Create your views here.
def index(request):
    this_week_special = ['Truffle Risotto', 'Grilled Octopus', 'Chocolate Soufflé']
    menu_items = Menu.objects.all()
    specials = Menu.objects.filter(name__in=this_week_special)
    gallery = list(Gallery.objects.all())
    shuffle(gallery)
    
    categories = [choice[0] for choice in Menu.CategoryChoices.choices]
    menu_by_category = []
    for category in categories:
        items = list(Menu.objects.filter(category=category, is_available=True))
        shuffle(items)
        menu_by_category.extend(items[:2])

    shuffle(menu_by_category)
    
    reviews = list(Review.objects.all())
    shuffle(reviews)
    
    context = {
        'menu_items': menu_by_category,
        'specials': specials,
        'gallery': gallery[:8],
        "reviews": reviews[:3],
    }
    return render(request, 'index.html', context)

def book_reservation(request):
    if request.method == 'POST':
        data = request.POST
        
        customer_name = data.get('name')
        customer_email = data.get('email')
        customer_phone = data.get('phone')
        number_of_guests = data.get('guests')
        reservation_date = data.get('date')
        reservation_time = data.get('time')
        special_requests = data.get('special_request')

        Reservation.objects.create(
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            number_of_guests=number_of_guests,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            special_requests=special_requests
        )

    return JsonResponse({'status': "success", 'message': 'Reservation booked successfully!'})
def contact_us(request):
    if request.method == 'POST':
        data = request.POST
        
        customer_name = data.get('contact_name')
        customer_email = data.get('contact_email')
        subject = data.get('contact_subject')
        message = data.get('contact_message')

        Contact.objects.create(
            customer_name=customer_name,
            customer_email=customer_email,
            subject=subject,
            message=message,
            contact_date=datetime.now().date(),
        )

    return JsonResponse({'status': "success", 'message': 'Message was sent successfully!'})


