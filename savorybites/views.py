import json, requests
from datetime import datetime
from random import shuffle
from decouple import config
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
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

def add_to_cart(request):
    if request.method == 'POST':
        menu_item_id = request.POST.get('menu_item_id')
        menu_item = get_object_or_404(Menu, id=menu_item_id)

        if request.user.is_authenticated:
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                menu_item=menu_item,
                defaults={'quantity': 1}
            )
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.save()
                session_key = request.session.session_key

            cart_item, created = CartItem.objects.get_or_create(
                session_key=session_key,
                menu_item=menu_item,
                defaults={'quantity': 1}
            )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        subtotal = float(cart_item.menu_item.price * cart_item.quantity)

        if request.user.is_authenticated:
            cart_count = CartItem.objects.filter(user=request.user).count()
        else:
            cart_count = CartItem.objects.filter(session_key=session_key).count()

        return JsonResponse({
            'status': 'success',
            'message': 'Item added to cart!',
            'quantity': cart_item.quantity,
            'subtotal': subtotal,
            'cart_count': cart_count
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def remove_from_cart(request, cart_item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=cart_item_id)

        if request.user.is_authenticated:
            if cart_item.user != request.user:
                return JsonResponse({'status': 'error', 'message': 'Cart item does not belong to this user'})
            cart_item.delete()
            remaining_items = CartItem.objects.filter(user=request.user)

        else:
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
            'total': float(total)
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def update_cart_quantity(request, cart_item_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_quantity = data.get('quantity')

            if not isinstance(new_quantity, (int, float)) or new_quantity < 1:
                return JsonResponse({'status': 'error', 'message': 'Quantity must be a positive number'})

            cart_item = get_object_or_404(CartItem, id=cart_item_id)

            if request.user.is_authenticated:
                if cart_item.user != request.user:
                    return JsonResponse({'status': 'error', 'message': 'Cart item does not belong to this user'})
            else:
                session_key = request.session.session_key
                if not session_key:
                    return JsonResponse({'status': 'error', 'message': 'Session not found'})
                if cart_item.session_key != session_key:
                    return JsonResponse({'status': 'error', 'message': 'Cart item does not belong to this session'})

            # Update quantity
            cart_item.quantity = int(new_quantity)
            cart_item.save()

            # Recalculate total
            if request.user.is_authenticated:
                remaining_items = CartItem.objects.filter(user=request.user)
            else:
                remaining_items = CartItem.objects.filter(session_key=session_key)

            total = sum(item.menu_item.price * item.quantity for item in remaining_items)

            return JsonResponse({
                'status': 'success',
                'message': 'Quantity updated',
                'quantity': cart_item.quantity,
                'subtotal': float(cart_item.menu_item.price * cart_item.quantity),
                'total': float(total),
                'price': float(cart_item.menu_item.price)
            })

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def clear_cart(request):
    if request.method == 'POST':
        try:
            if request.user.is_authenticated:
                CartItem.objects.filter(user=request.user).delete()
            else:
                session_key = request.session.session_key
                if not session_key:
                    return JsonResponse({'status': 'error', 'message': 'Session not found'})

                CartItem.objects.filter(session_key=session_key, user__isnull=True).delete()

            return JsonResponse({
                'status': 'success',
                'message': 'Cart cleared successfully',
                'total': 0,
                'cart_count': 0
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def view_cart(request):
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            return render(request, 'utilities/cart.html', {'cart_items': [], 'total': 0, 'cart_count': 0})

        cart_items = CartItem.objects.filter(session_key=session_key, user__isnull=True)

    cart_count = cart_items.count()
    total = sum(item.menu_item.price * item.quantity for item in cart_items)

    return render(request, 'utilities/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count,
    })

def checkout(request):
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

        # Optional: Assign user to the order if logged in
        if request.user.is_authenticated:
            order.user = request.user
            order.save()

        # Clear cart
        # cart_items.delete()

        messages.success(request, 'Order created successfully! Please proceed to payment.')
        return redirect('payment', order_id=order.id)

    return render(request, 'utilities/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count,
    })

@login_required
@csrf_protect
def payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)

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

        usd_amount = float(order.total_price)
        exchange_rate = 1645
        ngn_amount = usd_amount * exchange_rate
        amount_in_kobo = int(ngn_amount * 100)

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
                    amount=order.total_price,
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

    return render(request, 'utilities/payment.html', {
        'order': order,
        'cart_count': cart_count,
        'PAYSTACK_PUBLIC_KEY': config('PAYSTACK_PUBLIC_KEY')
    })

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
                payment_method = response['data'].get('channel', 'card')
                payment = Payment.objects.get(reference=reference)
                payment.status = 'completed'
                payment.payment_method=payment_method
                payment.save()
                
                # Update order status
                order = payment.order
                order.payment_status = 'paid'
                order.status = 'confirmed'
                order.save()
                
                # Create Order Delivery
                Delivery.objects.create(
                    order=order,
                    delivery_date=datetime.now().date(),
                )
                
                # Send success message
                messages.success(request, 'Payment successful! Your order has been confirmed.')
                return redirect('profile')
            else:
                messages.error(request, 'Payment verification failed')
                return redirect('payment', order_id=order.id)
                
        except Exception as e:
            messages.error(request, f'Payment verification failed: {str(e)}')
            return redirect('payment', order_id=order.id)

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
    # Ensure session exists for guest users
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
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('signup')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return redirect('signup')
        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters long')
            return redirect('signup')
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long')
            return redirect('signup')
        if not username.isalnum():
            messages.error(request, 'Username must be alphanumeric')
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

         # Paginate orders
        orders_paginator = Paginator(orders, 4)
        orders_page_number = request.GET.get('orders_page')
        orders_page_obj = orders_paginator.get_page(orders_page_number)

        # Paginate payments
        payments_paginator = Paginator(payments, 4)
        payments_page_number = request.GET.get('payments_page')
        payments_page_obj = payments_paginator.get_page(payments_page_number)
        
        
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

        return render(request, 'utilities/profile.html', {
            'profile': profile,
            'orders': orders_page_obj,
            'payments': payments_page_obj,
            'cart_count': cart_count
        })
        

