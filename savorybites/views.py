from datetime import datetime
from decouple import config
from random import shuffle
import requests, json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from savorybites.models import (
    Menu, Contact, Gallery, Reservation, Review,
    CartItem, Order, Payment, Profile, Special
)
from datetime import datetime

# Create your views here.
def index(request):
    # Get today's date
    today = datetime.now().date()

    # Get today's special
    specials = Special.objects.select_related('menu_item')
    
    # Get menu items
    menu_items = Menu.objects.filter(is_available=True).prefetch_related('specials')
    
    # Get gallery images
    gallery = list(Gallery.objects.all())
    shuffle(gallery)
    
    # Get reviews
    reviews = list(Review.objects.all())
    shuffle(reviews)
    
    # Get featured menu items (one from each category)
    categories = Menu.CategoryChoices.choices
    featured_items = {}
    for category in categories:
        items = Menu.objects.filter(category=category[0], is_available=True)
        if items.exists():
            featured_items[category[0]] = items.first()
    
    # Get cart count from database
    session_key = request.session.session_key
    if session_key:
        cart_count = CartItem.objects.filter(session_key=session_key).count()
    else:
        cart_count = 0

    context = {
        'menu_items': menu_items,
        'specials': specials,
        'gallery': gallery[:8],
        'reviews': reviews[:3],
        'featured_items': featured_items,
        'cart_count': cart_count
    }
    return render(request, 'index.html', context)

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

def add_to_cart(request):
    if request.method == 'POST':
        menu_item_id = request.POST.get('menu_item_id')
        menu_item = get_object_or_404(Menu, id=menu_item_id)
        
        # Get or create session key
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
            
        # Create or update cart item
        cart_item, created = CartItem.objects.get_or_create(
            session_key=session_key,
            menu_item=menu_item,
            defaults={'quantity': 1}
        )
        
        if not created:
            # If item already exists, increment quantity
            cart_item.quantity += 1
            cart_item.save()
            
        # Calculate subtotal
        subtotal = float(cart_item.menu_item.price * cart_item.quantity)
        
        # Get cart count
        cart_count = CartItem.objects.filter(session_key=session_key).count()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Item added to cart successfully!',
            'quantity': cart_item.quantity,
            'subtotal': subtotal,
            'cart_count': cart_count
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def remove_from_cart(request, cart_item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=cart_item_id)
        session_key = request.session.session_key
        if not session_key:
            return JsonResponse({'status': 'error', 'message': 'Session not found'})
        
        if cart_item.session_key != session_key:
            return JsonResponse({'status': 'error', 'message': 'Cart item does not belong to this session'})
            
        cart_item.delete()
        remaining_items = CartItem.objects.filter(session_key=session_key)
        total = sum(item.menu_item.price * item.quantity for item in remaining_items)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Item removed from cart',
            'cart_count': remaining_items.count(),
            'total': total
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def update_cart_quantity(request, cart_item_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_quantity = data.get('quantity')

            if not isinstance(new_quantity, (int, float)) or new_quantity < 1:
                return JsonResponse({'status': 'error', 'message': 'Quantity must be a positive number'})
                
            cart_item = get_object_or_404(CartItem, id=cart_item_id)
            session_key = request.session.session_key
            if not session_key:
                return JsonResponse({'status': 'error', 'message': 'Session not found'})
            
            if cart_item.session_key != session_key:
                return JsonResponse({'status': 'error', 'message': 'Cart item does not belong to this session'})
                
            cart_item.quantity = int(new_quantity)
            cart_item.save()
            
            # Calculate new total
            remaining_items = CartItem.objects.filter(session_key=session_key)
            total = sum(item.menu_item.price * item.quantity for item in remaining_items)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Quantity updated',
                'quantity': cart_item.quantity,
                'subtotal': float(cart_item.menu_item.price * cart_item.quantity),
                'total': total,
                'price': float(cart_item.menu_item.price)
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

def clear_cart(request):
    if request.method == 'POST':
        try:
            session_key = request.session.session_key
            if not session_key:
                return JsonResponse({'status': 'error', 'message': 'Session not found'})
            
            # Delete all cart items for this session
            CartItem.objects.filter(session_key=session_key).delete()
            
            # Return success response with updated totals
            return JsonResponse({
                'status': 'success',
                'message': 'Cart cleared successfully',
                'total': 0,
                'cart_count': 0
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

def view_cart(request):
    session_key = request.session.session_key
    if not session_key:
        return render(request, 'utilities/cart.html', {'cart_items': [], 'total': 0})
        
    cart_items = CartItem.objects.filter(session_key=session_key)
    cart_count = cart_items.count() if cart_items.exists() else 0
    total = sum(item.menu_item.price * item.quantity for item in cart_items)
    
    return render(request, 'utilities/cart.html', {
        'total': total,
        'cart_items': cart_items,
        'cart_count': cart_count,
    })

def checkout(request):
    session_key = request.session.session_key
    
    if not session_key:
        messages.error(request, 'Your cart is empty')
        return redirect('menu')
        
    cart_items = CartItem.objects.filter(session_key=session_key)
    cart_count = cart_items.count() if cart_items.exists() else 0
    # messages.error(request, 'Your cart is empty')
    # return redirect('menu')
    
    total = sum(item.menu_item.price * item.quantity for item in cart_items)
    
    if request.method == 'POST':
        # Create order
        order = Order.objects.create(
            customer_name=request.POST.get('full_name'),
            customer_email=request.POST.get('email'),
            customer_phone=request.POST.get('phone'),
            customer_address=request.POST.get('address'),
            delivery_option=request.POST.get('delivery_option'),
            special_instructions=request.POST.get('notes', ''),
            total_price=total,
            status='pending',
            payment_status='pending'
        )
        
        # Set cart items for the order
        order.cart_items.set(cart_items)
        
        # Clear cart
        # cart_items.delete()
        
        messages.success(request, 'Order created successfully! Please proceed to payment.')
        return redirect('payment', order_id=order.id)
        
    return render(request, 'utilities/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count,
    })

@csrf_exempt
def payment(request, order_id):
    try:
        session_key = request.session.session_key
        order = Order.objects.get(id=order_id)
        
        if request.method == 'POST':
            if order.payment_status != 'pending':
                return JsonResponse({'status': 'error', 'message': 'Order already paid'})
                
            # Get order details from POST data
            email = request.POST.get('customer_email')

            # Convert amount to kobo
            amount = int(order.total_price) * 100 
            
            if not email:
                return JsonResponse({'status': 'error', 'message': 'Customer email is required'})
                
            # Initialize Paystack payment
            headers = {
                'Authorization': f'Bearer {config("PAYSTACK_SECRET_KEY").strip()}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            data = {
                'email': email,
                'amount': amount*1645,
                'callback_url': 'http://127.0.0.1:8000/verify/',
                'metadata': {
                    'order_id': order.id,
                }
            }
            
            response = requests.post(
                'https://api.paystack.co/transaction/initialize',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result['status']:
                    # Create payment record
                    Payment.objects.create(
                        order=order,
                        amount=order.total_price,
                        payment_method='card',
                        status='pending',
                        reference=result['data']['reference']
                    )
                    
                    json_response = JsonResponse({
                        'status': 'success',
                        'message': 'Payment initialized successfully',
                        'authorization_url': result['data']['authorization_url'],
                        'reference': result['data']['reference']
                    })
                    json_response['Access-Control-Allow-Origin'] = '*'
                    return json_response
                else:
                    error_msg = result.get('message', 'Payment initialization failed')
                    json_response = JsonResponse({
                        'status': 'error',
                        'message': error_msg
                    })
                    json_response['Access-Control-Allow-Origin'] = '*'
                    return json_response
            else:
                error_msg = response.json().get('message', 'Failed to connect to Paystack')
                json_response = JsonResponse({
                    'status': 'error',
                    'message': error_msg
                })
                json_response['Access-Control-Allow-Origin'] = '*'
                return json_response
        if session_key:
            cart_items = CartItem.objects.filter(session_key=session_key)
            cart_count = cart_items.count() if cart_items.exists() else 0

        # Handle GET request - render the payment template
        context = {
            'order': order,
            'cart_count': cart_count,
            'PAYSTACK_PUBLIC_KEY': config('PAYSTACK_PUBLIC_KEY')
        }
        return render(request, 'utilities/payment.html', context)
        
    except Order.DoesNotExist:
        json_response = JsonResponse({'status': 'error', 'message': 'Order not found'})
        json_response['Access-Control-Allow-Origin'] = '*'
        return json_response
    except Exception as e:
        json_response = JsonResponse({'status': 'error', 'message': str(e)})
        json_response['Access-Control-Allow-Origin'] = '*'
        return json_response
 
def payment_callback(request):
    # Get reference from Paystack
    reference = request.GET.get('reference')
    
    if reference:
        try:
            # Verify payment
            headers = {
                'Authorization': f'Bearer {config("PAYSTACK_SECRET_KEY")}',
                'Content-Type': 'application/json',
            }
            response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
            response = response.json()
            
            if response['status'] and response['data']['status'] == 'success':
                # Update payment status
                payment = Payment.objects.get(reference=reference)
                payment.status = 'completed'
                payment.save()
                
                # Update order status
                order = payment.order
                order.payment_status = 'paid'
                order.status = 'confirmed'
                order.save()
                
                # Send success message
                messages.success(request, 'Payment successful! Your order has been confirmed.')
                return redirect('orders')
            else:
                messages.error(request, 'Payment verification failed')
                return redirect('payment', order_id=order.id)
                
        except Exception as e:
            messages.error(request, f'Payment verification failed: {str(e)}')
            return redirect('payment', order_id=order.id)

def orders(request):
    # orders = Order.objects.filter(
    #     Q(customer_email=request.user.email) if request.user.is_authenticated else Q(session_key=request.session.session_key)
    # ).order_by('-order_date')

    orders = Order.objects.filter(
        Q(customer_email=request.user.email) if request.user.is_authenticated else Q(session_key=request.session.session_key)
    ).order_by('-order_date')
    
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key
    
    cart_items = CartItem.objects.filter(session_key=session_key)
    cart_count = cart_items.count() if cart_items.exists() else 0
    
    return render(request, 'utilities/orders.html', {
        'orders': page_obj,
        'cart_count': cart_count
    })

def menu(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key
    
    categories = Menu.CategoryChoices.choices
    menu_items = Menu.objects.filter(is_available=True)
    
    category = request.GET.get('category')
    if category and category in dict(Menu.CategoryChoices.choices):
        menu_items = menu_items.filter(category=category)

    cart_items = CartItem.objects.filter(session_key=session_key)
    cart_count = cart_items.count() if cart_items.exists() else 0
    
    return render(request, 'layout.html', {
        'menu_items': menu_items,
        'categories': categories,
        'cart_count': cart_count,
    })

def contact_us(request):
    if request.method == 'POST':
        Contact.objects.create(
            customer_name=request.POST.get('contact_name'),
            customer_email=request.POST.get('contact_email'),
            subject=request.POST.get('contact_subject'),
            message=request.POST.get('contact_message')
        )
        messages.success(request, 'Message sent successfully!')
        return redirect('contact_us')
    return render(request, 'utilities/contact.html')

def book_reservation(request):
    if request.method == 'POST':
        Reservation.objects.create(
            customer_name=request.POST.get('name'),
            customer_email=request.POST.get('email'),
            customer_phone=request.POST.get('phone'),
            number_of_guests=request.POST.get('guests'),
            reservation_date=request.POST.get('date'),
            reservation_time=request.POST.get('time'),
            special_requests=request.POST.get('special_request', '')
        )
        messages.success(request, 'Reservation booked successfully!')
        return redirect('reservations')
    return render(request, 'utilities/reservation.html')

def reservations(request):
    if request.user.is_authenticated:
        reservations = Reservation.objects.filter(
            customer_email=request.user.email
        ).order_by('-reservation_date')
        return render(request, 'utilities/reservations.html', {
            'reservations': reservations
        })
    return redirect('login')

def reviews(request):
    if request.method == 'POST':
        Review.objects.create(
            customer_name=request.POST.get('name'),
            customer_occupation=request.POST.get('occupation'),
            rating=request.POST.get('rating'),
            comment=request.POST.get('comment')
        )
        messages.success(request, 'Review submitted successfully!')
        return redirect('reviews')
    
    reviews = Review.objects.all().order_by('-review_date')
    return render(request, 'utilities/reviews.html', {
        'reviews': reviews
    })

def gallery(request):
    gallery_items = Gallery.objects.all().order_by('-upload_date')
    return render(request, 'utilities/gallery.html', {
        'gallery': gallery_items
    })

def profile(request):
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=request.user)
            
        if request.method == 'POST':
            profile.phone_number = request.POST.get('phone_number')
            profile.address = request.POST.get('address')
            profile.preferred_payment_method = request.POST.get('preferred_payment_method')
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
            
        return render(request, 'utilities/profile.html', {
            'profile': profile
        })
    return redirect('login')

