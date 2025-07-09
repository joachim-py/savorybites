import json, requests
from datetime import datetime
from random import shuffle
from decouple import config
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_protect, csrf_exempt 
from savorybites.models import (CartItem, Contact, Delivery, Gallery, Menu, Order,
                                Payment, Profile, Reservation, Review, Special)

    
def index(request):
    today = datetime.now().date()

    specials = Special.objects.select_related('menu_item')
    menu_items = Menu.objects.filter(is_available=True).prefetch_related('specials')

    gallery = list(Gallery.objects.all())
    shuffle(gallery)

    reviews = list(Review.objects.all())
    shuffle(reviews)

    categories = Menu.CategoryChoices.choices
    featured_items = {}
    for category in categories:
        items = Menu.objects.filter(category=category[0], is_available=True)
        if items.exists():
            featured_items[category[0]] = items.first()

    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(user=request.user).count()
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
        cart_count = CartItem.objects.filter(session_key=session_key, user__isnull=True).count()

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

@require_POST
def add_to_cart(request):
    try:
        menu_item_id = request.POST.get('menu_item_id')
        if not menu_item_id:
            return JsonResponse({'status': 'error', 'message': 'Menu item ID required'}, status=400)
            
        menu_item = get_object_or_404(Menu, id=menu_item_id)
        
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        # Get or create cart item
        if request.user.is_authenticated:
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                menu_item=menu_item,
                defaults={'quantity': 1}
            )
        else:
            cart_item, created = CartItem.objects.get_or_create(
                session_key=session_key,
                menu_item=menu_item,
                defaults={'quantity': 1}
            )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        # Calculate cart count
        if request.user.is_authenticated:
            cart_count = CartItem.objects.filter(user=request.user).count()
        else:
            cart_count = CartItem.objects.filter(session_key=session_key).count()

        response_data = {
            'status': 'success',
            'message': 'Item added to cart',
            'cart_count': cart_count,
            'item': {
                'id': cart_item.id,
                'name': menu_item.name,
                'quantity': cart_item.quantity,
                'price': str(menu_item.price),
                'subtotal': str(menu_item.price * cart_item.quantity)
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
def remove_from_cart(request, cart_item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=cart_item_id)
        
        # Verify ownership
        if request.user.is_authenticated:
            if cart_item.user != request.user:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
            items = CartItem.objects.filter(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key or cart_item.session_key != session_key:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
            items = CartItem.objects.filter(session_key=session_key)
        
        # Delete item and calculate new totals
        cart_item.delete()
        remaining_items = items.exclude(id=cart_item_id)
        
        response_data = {
            'status': 'success',
            'message': 'Item removed from cart',
            'item_id': cart_item_id,
            'cart_count': remaining_items.count(),
            'total': float(sum(item.menu_item.price * item.quantity for item in remaining_items))
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
def update_cart_quantity(request, cart_item_id):
    try:
        data = json.loads(request.body)
        new_quantity = int(data.get('quantity', 1))
        
        if new_quantity < 1:
            return JsonResponse({'status': 'error', 'message': 'Quantity must be at least 1'}, status=400)
            
        cart_item = get_object_or_404(CartItem, id=cart_item_id)
        
        # Verify ownership
        if request.user.is_authenticated:
            if cart_item.user != request.user:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
            items = CartItem.objects.filter(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key or cart_item.session_key != session_key:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
            items = CartItem.objects.filter(session_key=session_key)
        
        # Update quantity
        cart_item.quantity = new_quantity
        cart_item.save()
        
        # Calculate response data
        response_data = {
            'status': 'success',
            'message': 'Quantity updated',
            'item_id': cart_item_id,
            'quantity': new_quantity,
            'price': float(cart_item.menu_item.price),
            'subtotal': float(cart_item.menu_item.price * new_quantity),
            'total': float(sum(item.menu_item.price * item.quantity for item in items)),
            'cart_count': items.count()
        }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
def clear_cart(request):
    try:
        if request.user.is_authenticated:
            CartItem.objects.filter(user=request.user).delete()
            cart_count = 0
        else:
            session_key = request.session.session_key
            if not session_key:
                return JsonResponse({'status': 'error', 'message': 'Session not found'}, status=400)
                
            CartItem.objects.filter(session_key=session_key).delete()
            cart_count = 0
        
        return JsonResponse({
            'status': 'success',
            'message': 'Cart cleared',
            'cart_count': cart_count,
            'total': 0
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def view_cart(request):
    # Get cart items based on authentication status
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user).select_related('menu_item')
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart_items = CartItem.objects.filter(session_key=session_key, user__isnull=True).select_related('menu_item')

    # Calculate totals
    cart_count = cart_items.count()
    total = sum(item.menu_item.price * item.quantity for item in cart_items)

    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count,
    }

    return render(request, 'utilities/cart.html', context)

@login_required
def checkout(request):
    try:
        # Get cart items
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.save()
                session_key = request.session.session_key
            cart_items = CartItem.objects.filter(session_key=session_key, user__isnull=True)

        if not cart_items.exists():
            messages.error(request, 'Your cart is empty.')
            return redirect('menu')

        cart_count = cart_items.count()
        total = sum(item.menu_item.price * item.quantity for item in cart_items) 

        print('GET CART ITEMS:', cart_items)
        
        if request.method == 'POST':
            try:
                # Validate required fields
                required_fields = {
                    'full_name': 'Full name',
                    'email': 'Email address',
                    'phone': 'Phone number',
                    'delivery_option': 'Delivery option'
                }
                
                errors = []
                for field, name in required_fields.items():
                    if not request.POST.get(field):
                        errors.append(f"{name} is required")
                
                # Additional validation for delivery address if delivery is selected
                if request.POST.get('delivery_option') == 'delivery' and not request.POST.get('address'):
                    errors.append("Delivery address is required when selecting delivery option")
                
                if errors:
                    for error in errors:
                        messages.error(request, error)
                    return redirect('checkout')

                try:
                    # Create order
                    order = Order.objects.create(
                        customer_name=request.POST.get('full_name').strip(),
                        customer_email=request.POST.get('email').strip(),
                        customer_phone=request.POST.get('phone').strip(),
                        customer_address=request.POST.get('address', '').strip(),
                        delivery_option=request.POST.get('delivery_option'),
                        special_instructions=request.POST.get('notes', '').strip(),
                        total_price=total,
                        status='pending',
                        payment_status='pending',
                        user=request.user if request.user.is_authenticated else None
                    )

                    # Add cart items to order
                    order.cart_items.set(cart_items)
                    
                    # Clear the cart after successful order
                    # cart_items.delete()
                    
                    messages.success(request, 'Order created successfully! Please proceed to payment.')
                    return redirect('payment', order_id=order.id)
                    
                except Exception as e:
                    messages.error(request, f'Error creating order: {str(e)}')
                    return redirect('checkout')
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
                return redirect('checkout')
    except Exception as e:
        messages.error(request, f'Error creating order: {str(e)}')
        return redirect('checkout')

    return render(request, 'utilities/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count,
    })

@login_required
@csrf_protect
def payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if order.delivery_option == 'delivery':
        total_amount = order.total_price + (2800 if order.total_price > 9000 and order.total_price < 450000 else 1500)
    else:
        total_amount = order.total_price

    if not request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)
        else:
            return redirect('login')
    
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(user=request.user).count()
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
        cart_count = CartItem.objects.filter(session_key=session_key, user__isnull=True).count()
    
    if request.method == 'POST':
        if order.payment_status != 'pending':
            return JsonResponse({'status': 'error', 'message': 'Order already paid'})

        email = request.POST.get('customer_email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'Customer email is required'})

        amount = float(total_amount)
        amount_in_kobo = int(amount * 100)

        headers = {
            'Authorization': f'Bearer {config("PAYSTACK_SECRET_KEY").strip()}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        data = {
            'email': email,
            'amount': amount_in_kobo,
            'callback_url': 'http://127.0.0.1:8000/verify/',
            'metadata': {
                'order_id': order.id,
            }
        }

        try:
            response = requests.post(
                'https://api.paystack.co/transaction/initialize',
                headers=headers,
                json=data
            )

            result = response.json()
            if response.status_code == 200 and result['status']:
                Payment.objects.create(
                    order=order,
                    amount=total_amount,
                    payment_method='card',
                    status='pending',
                    reference=result['data']['reference']
                )
                return JsonResponse({
                    'status': 'success',
                    'message': 'Payment initialized successfully',
                    'authorization_url': result['data']['authorization_url'],
                    'reference': result['data']['reference']
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': result.get('message', 'Payment initialization failed')
                })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    print(total_amount)
    return render(request, 'utilities/payment.html', {
        'order': order,
        'cart_count': cart_count,
        'total_amount': total_amount,
        'PAYSTACK_PUBLIC_KEY': config('PAYSTACK_PUBLIC_KEY')
    })

# def payment_callback(request):
#     # Get reference from Paystack
#     reference = request.GET.get('reference')
    
#     if reference:
#         try:
#             # Verify payment
#             headers = {
#                 'Authorization': f'Bearer {config("PAYSTACK_SECRET_KEY")}',
#                 'Content-Type': 'application/json',
#             }
#             response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
#             response = response.json()
            
#             if response['status'] and response['data']['status'] == 'success':
#                 # Update payment status
#                 payment_method = response['data'].get('channel', 'card')
#                 payment = Payment.objects.get(reference=reference)
#                 payment.status = 'completed'
#                 payment.payment_method=payment_method
#                 payment.save()
                
#                 # Update order status
#                 order = payment.order
#                 order.payment_status = 'paid'
#                 order.status = 'confirmed'
#                 order.save()
                
#                 # Create Order Delivery
#                 Delivery.objects.create(
#                     order=order,
#                     delivery_date=datetime.now().date(),
#                 )
                
#                 # Send success message
#                 messages.success(request, 'Payment successful! Your order has been confirmed.')
#                 return redirect('profile')
#             else:
#                 messages.error(request, 'Payment verification failed')
#                 return redirect('payment', order_id=order.id)
                
#         except Exception as e:
#             messages.error(request, f'Payment verification failed: {str(e)}')
#             return redirect('payment', order_id=order.id)

def payment_callback(request):
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
                payment_method = response['data'].get('channel', 'card')
                payment = Payment.objects.get(reference=reference)
                payment.status = 'completed'
                payment.payment_method = payment_method
                payment.save()
                
                # Update order status
                order = payment.order
                
                if order.delivery_option == 'delivery':
                    total_amount = order.total_price + (2800 if order.total_price > 9000 and order.total_price < 450000 else 1500)
                else:
                    total_amount = order.total_price
                
                order.delivery_price = total_amount
                order.payment_status = 'paid'
                order.status = 'confirmed'
                order.save()
                
                # Clear cart AFTER successful payment
                if order.user:
                    CartItem.objects.filter(user=order.user).delete()
                
                # Create Order Delivery
                Delivery.objects.create(
                    order=order,
                    delivery_date=datetime.now().date(),
                )
                
                messages.success(request, 'Payment successful! Your order has been confirmed.')
                return redirect('profile')
            else:
                messages.error(request, 'Payment verification failed')
                return redirect('payment', order_id=payment.order.id)
                
        except Payment.DoesNotExist:
            messages.error(request, 'Payment record not found')
            return redirect('menu')
        except Exception as e:
            messages.error(request, f'Payment verification failed: {str(e)}')
            return redirect('menu')
    
    messages.error(request, 'Invalid payment reference')
    return redirect('menu')

@login_required
def orders(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by('-order_date')
        cart_items = CartItem.objects.filter(user=request.user)
    else:
        orders = Order.objects.filter(session_key=session_key).order_by('-order_date')
        cart_items = CartItem.objects.filter(session_key=session_key, user__isnull=True)

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    cart_count = cart_items.count()

    return render(request, 'utilities/orders.html', {
        'orders': page_obj,
        'cart_count': cart_count
    })

@login_required
def order_details_json(request, order_id):
    try:
        order = get_object_or_404(Order, pk=order_id)

        # check if user or session matches the order
        if request.user.is_authenticated:
            if order.user != request.user:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized access'}, status=403)
        else:
            session_key = request.session.session_key
            if not session_key or order.session_key != session_key:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized access'}, status=403)

        items = [{
            'name': item.menu_item.name,
            'quantity': item.quantity,
            'price': float(item.menu_item.price),
            'subtotal': float(item.menu_item.price * item.quantity)
        } for item in order.cart_items.all()]

        return JsonResponse({
            'status': 'success',
            'order': {
                'id': order.id,
                'order_date': order.order_date.strftime('%Y-%m-%d'),
                'status': order.status,
                'payment_status': order.payment_status,
                'total_price': float(order.total_price)
            },
            'items': items
        })

    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)

def menu(request):
    # Ensuring session exists for guest users
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    # Get menu categories and items
    categories = Menu.CategoryChoices.choices
    menu_items = Menu.objects.filter(is_available=True)

    # Filter by category if provided
    category = request.GET.get('category')
    if category and category in dict(Menu.CategoryChoices.choices):
        menu_items = menu_items.filter(category=category)
        
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
    else:
        cart_items = CartItem.objects.filter(session_key=session_key, user__isnull=True)

    cart_count = cart_items.count()
    
    context = {
        'menu_items': menu_items,
        'categories': categories,
        'cart_count': cart_count,
        'title': 'Menu',
        'description': 'Explore our menu of delectable dishes.',
        'hero_image': 'menu_banner.jpg'
    }

    return render(request, 'layout.html', context)

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
    context = {
        'title': 'Contact Us',
        'description': 'Contact us for any inquiries or feedback.',
        'hero_image': 'contact_banner.jpg'
    }
    return render(request, 'utilities/contact.html', context)

@require_http_methods(["POST"])
def book_reservation(request):
    try:
        # Get form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        guests = request.POST.get('guests')
        date = request.POST.get('date')
        time = request.POST.get('time')
        special_requests = request.POST.get('special_request', '')
        
        # Input validation
        if not all([name, email, phone, guests, date, time]):
            return JsonResponse({'status': 'error', 'message': 'All fields are required'}, status=400)
            
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'status': 'error', 'message': 'Please enter a valid email address'}, status=400)
            
        # Create reservation
        reservation = Reservation.objects.create(
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            number_of_guests=guests,
            reservation_date=date,
            reservation_time=time,
            special_requests=special_requests,
            user=request.user
        )
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Your reservation has been booked successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def reservations(request):
    if request.user.is_authenticated:
        reservations = Reservation.objects.filter(
            user=request.user
        ).order_by('-reservation_date')        
        return render(request, 'utilities/reservations.html', {
            'reservations': reservations,
            'title': 'Reservations',
            'description': 'Make your reservations here',
            'hero_image': 'reservation_banner.jpg'
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
    context = {
        'gallery': gallery_items,
        'title': 'Gallery',
        'description': 'Our Gallery',
        'hero_image': 'gallery_banner.jpg'
    }
    return render(request, 'utilities/gallery.html', context)

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        next_url = request.POST.get('next') or 'index'
        login_source = request.POST.get('login_source')
        
        user = authenticate(username=username, password=password)
        if user is not None:
            session_key = request.session.session_key
            if session_key:
                session_cart_items = CartItem.objects.filter(session_key=session_key, user__isnull=True)

                for item in session_cart_items:
                    existing = CartItem.objects.filter(user=user, menu_item=item.menu_item).first()
                    if existing:
                        existing.quantity += item.quantity
                        existing.save()
                        item.delete()
                    else:
                        item.user = user
                        item.session_key = None
                        item.save()

            auth_login(request, user)
            request.session.set_expiry(0 if not remember else 1209600)

            # messages.success(request, 'Logged in successfully!')

            if login_source == 'modal' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect_url': next_url})

            return redirect(next_url)
        else:
            if login_source == 'modal' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Invalid username or password'})
            messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')

@login_required
def logout(request):
    user = request.user
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    if user.is_authenticated:
        user_cart_items = CartItem.objects.filter(user=user)

        for item in user_cart_items:
            session_item = CartItem.objects.filter(session_key=session_key, menu_item=item.menu_item, user__isnull=True).first()
            if session_item:
                session_item.quantity += item.quantity
                session_item.save()
                item.delete()
            else:
                item.session_key = session_key
                item.user = None
                item.save()

    auth_logout(request)
    return redirect('login')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validate required fields
        if not all([username, email, password, confirm_password]):
            messages.error(request, 'All fields are required')
            return redirect('signup')
            
        # Validate email format
        if '@' not in email or '.' not in email.split('@')[-1]:
            messages.error(request, 'Please enter a valid email address')
            return redirect('signup')
            
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('signup')
            
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return redirect('signup')
            
        # Validate username
        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters long')
            return redirect('signup')
            
        if not username.isalnum():
            messages.error(request, 'Username must be alphanumeric')
            return redirect('signup')
            
        # Validate password
        if not password:
            messages.error(request, 'Password is required')
            return redirect('signup')
            
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long')
            return redirect('signup')
            
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return redirect('signup')

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            Profile.objects.create(user=user)
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('signup')

    return render(request, 'signup.html')

@login_required
def profile(request):
    # Ensure session exists for guests
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
    else:
        cart_items = CartItem.objects.filter(session_key=session_key, user__isnull=True)

    cart_count = cart_items.count()

    # only authenticated users can access profile
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=request.user)

        orders = Order.objects.filter(user=request.user).order_by('-order_date')
        payments = Payment.objects.filter(order__user=request.user).order_by('-payment_date')
        reservations = Reservation.objects.filter(user=request.user).order_by('-created_at')

        # Paginate orders
        orders_paginator = Paginator(orders, 4)
        orders_page_number = request.GET.get('orders_page')
        orders_page_obj = orders_paginator.get_page(orders_page_number)

        # Paginate payments
        payments_paginator = Paginator(payments, 4)
        payments_page_number = request.GET.get('payments_page')
        payments_page_obj = payments_paginator.get_page(payments_page_number)
        
        # Paginate reservations
        reservations_paginator = Paginator(reservations, 4)
        reservations_page_number = request.GET.get('reservations_page')
        reservations_page_obj = reservations_paginator.get_page(reservations_page_number)
        
        
        # ✏ Handle profile update
        if request.method == 'POST':
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')

            # Prevent duplicate emails
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.error(request, 'Email already in use')
                return redirect('profile')

            # Update user model
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.email = email
            request.user.save()

            # Update profile model
            profile.phone_number = request.POST.get('phone_number')
            profile.address = request.POST.get('address')
            profile.save()

            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')

        context = {
            'profile': profile,
            'orders': orders_page_obj,
            'payments': payments_page_obj,
            'reservations': reservations_page_obj,
            'cart_count': cart_count
        }
        return render(request, 'utilities/profile.html', context)
