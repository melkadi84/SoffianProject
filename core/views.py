from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.core.signing import Signer, BadSignature
from django.core.mail import send_mail
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from .models import Category, Product, Promotion, CustomUser, Order, OrderItem
from core.translations import _t

signer = Signer()

def store_view(request):
    """
    Homepage and main store listing. Supporting search and category filters.
    """
    categories = Category.objects.all()
    products_qs = Product.objects.filter(status='PUBLISHED')

    # Category Filtering
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products_qs = products_qs.filter(category=selected_category)

    # Search Query
    search_query = request.GET.get('search')
    if search_query:
        products_qs = products_qs.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )

    # Fetch active promotions for carousel banner display
    now = timezone.now()
    active_promos = Promotion.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    )[:3] # Grab top 3 to display in a gorgeous carousel banner

    context = {
        'categories': categories,
        'products': products_qs,
        'selected_category': selected_category,
        'search_query': search_query,
        'active_promotions': active_promos,
    }
    return render(request, 'core/store.html', context)


def product_detail_view(request, slug):
    """
    Displays detail of a single product. 
    Draft products are only visible to the owner.
    """
    # Owners can see draft products, normal users only published
    if request.user.is_authenticated and request.user.is_owner:
        product = get_object_or_404(Product, slug=slug)
    else:
        product = get_object_or_404(Product, slug=slug, status='PUBLISHED')

    # Related products in the same category
    related_products = Product.objects.filter(
        category=product.category, 
        status='PUBLISHED'
    ).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'core/product_detail.html', context)


def signup_view(request):
    """
    Standard Email Signup. Generates verification link and logs email sending.
    """
    if request.user.is_authenticated:
        return redirect('store')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        
        if not username or not email or not password:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'core/signup.html')
            
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'core/signup.html')
            
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'core/signup.html')

        # Create inactive user (or active but unverified)
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone_number=phone,
            is_active=False, # disabled until email is verified
            email_verified=False,
            auth_provider='EMAIL'
        )
        
        # Generate token and sending link
        token = signer.sign(email)
        verify_url = request.build_absolute_uri(
            reverse('verify_email', kwargs={'token': token})
        )
        
        # Log to terminal (using console mail backend)
        try:
            send_mail(
                subject='Verify your Crafts Account',
                message=f'Hello {username},\n\nPlease verify your email by clicking: {verify_url}',
                from_email='noreply@crafts.com',
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, "Registration successful! A verification email has been simulated. Please check the server command line console for the verification link.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Error sending verification email: {str(e)}")
            
    return render(request, 'core/signup.html')


def verify_email_view(request, token):
    """
    Decodes verification token and activates the account.
    """
    try:
        email = signer.unsign(token, max_age=86400) # Valid for 24 hours
        user = get_object_or_404(CustomUser, email=email)
        user.is_active = True
        user.email_verified = True
        user.save()
        
        login(request, user)
        messages.success(request, f"Welcome to Crafts, {user.username}! Your email has been verified successfully.")
        return redirect('store')
    except BadSignature:
        messages.error(request, "The verification link is invalid or has expired.")
        return redirect('login')


def login_view(request):
    """
    Standard Email authentication logic.
    """
    if request.user.is_authenticated:
        return redirect('store')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, "Please enter both email and password.")
            return render(request, 'core/login.html')

        try:
            # Authenticate using email since email is the custom USERNAME_FIELD
            user = authenticate(request, email=email, password=password)
            if user is not None:
                if not user.email_verified:
                    # Provide token for unverified email in logs to make it easy to copy
                    token = signer.sign(user.email)
                    verify_url = request.build_absolute_uri(
                        reverse('verify_email', kwargs={'token': token})
                    )
                    print(f"\n[UNVERIFIED SIGNIN ATTEMPT] Verification Link: {verify_url}\n")
                    messages.warning(request, "Your email is not verified yet. We have logged a verification link in the console server logs for you.")
                    return render(request, 'core/login.html')
                    
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('store')
            else:
                messages.error(request, "Invalid email or password.")
        except Exception as e:
            messages.error(request, f"Login error: {str(e)}")

    return render(request, 'core/login.html')


def logout_view(request):
    """
    Standard logout route.
    """
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('store')


def mock_oauth_view(request, provider):
    """
    Mock endpoint simulating social signup/login (Google, Apple, Mobile Phone).
    """
    provider = provider.upper()
    if provider not in ['GOOGLE', 'APPLE', 'MOBILE']:
        messages.error(request, "Invalid authentication provider.")
        return redirect('login')

    # Build unique parameters based on provider selection
    phone = None
    if provider == 'GOOGLE':
        email = "google.user@gmail.com"
        username = "google_artisan"
    elif provider == 'APPLE':
        email = "apple.user@icloud.com"
        username = "apple_maker"
    else: # MOBILE
        phone = request.GET.get('phone', '0551234567')
        email = f"mobile.{phone}@crafts.com"
        username = f"mobile_{phone}"

    # Get or create the mock social user, instantly verified
    user, created = CustomUser.objects.get_or_create(
        email=email,
        defaults={
            'username': username,
            'is_active': True,
            'email_verified': True,
            'auth_provider': provider,
            'phone_number': phone if provider == 'MOBILE' else None
        }
    )

    login(request, user)
    msg = f"Signed up and logged in via {provider.capitalize()}!" if created else f"Logged in via {provider.capitalize()}!"
    messages.success(request, msg)
    return redirect('store')


def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    subtotal = Decimal('0.00')
    
    for prod_id, qty in list(cart.items()):
        try:
            product = Product.objects.get(id=int(prod_id), status='PUBLISHED')
            price = product.active_price
            item_total = price * int(qty)
            subtotal += item_total
            cart_items.append({
                'product': product,
                'quantity': qty,
                'price': price,
                'total': item_total,
            })
        except (Product.DoesNotExist, ValueError):
            if prod_id in cart:
                del cart[prod_id]
                request.session.modified = True

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
    }
    return render(request, 'core/cart.html', context)


def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, status='PUBLISHED')
    cart = request.session.get('cart', {})
    
    qty = 1
    if request.method == 'POST':
        try:
            qty = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            qty = 1
    else:
        try:
            qty = int(request.GET.get('quantity', 1))
        except (ValueError, TypeError):
            qty = 1
            
    prod_id_str = str(product.id)
    if prod_id_str in cart:
        new_qty = int(cart[prod_id_str]) + qty
        if new_qty <= 0:
            del cart[prod_id_str]
            messages.success(request, _t("Item removed from cart."))
        else:
            cart[prod_id_str] = new_qty
            if qty > 0:
                messages.success(request, _t("Added {} to your cart.", product.name))
            else:
                messages.success(request, _t("Item removed from cart.") if qty == -int(cart.get(prod_id_str, 0)) else _t("Updated cart quantity."))
    else:
        if qty > 0:
            cart[prod_id_str] = qty
            messages.success(request, _t("Added {} to your cart.", product.name))
        
    request.session['cart'] = cart
    request.session.modified = True
    
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('cart')


def cart_remove(request, product_id):
    cart = request.session.get('cart', {})
    prod_id_str = str(product_id)
    if prod_id_str in cart:
        del cart[prod_id_str]
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, _t("Item removed from cart."))
    return redirect('cart')


@login_required
def checkout_view(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, _t("Your cart is empty."))
        return redirect('store')
        
    cart_items = []
    subtotal = Decimal('0.00')
    for prod_id, qty in list(cart.items()):
        try:
            product = Product.objects.get(id=int(prod_id), status='PUBLISHED')
            price = product.active_price
            item_total = price * int(qty)
            subtotal += item_total
            cart_items.append({
                'product': product,
                'quantity': qty,
                'price': price,
                'total': item_total,
            })
        except (Product.DoesNotExist, ValueError):
            if prod_id in cart:
                del cart[prod_id]
                request.session.modified = True
                
    if not cart_items:
        messages.error(request, _t("Your cart is empty or products are no longer available."))
        return redirect('store')

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        phone_number = request.POST.get('phone_number')
        screenshot = request.FILES.get('payment_screenshot')
        
        if not full_name or not address or not phone_number or not screenshot:
            messages.error(request, _t("Please fill in all details and upload the Instapay payment receipt screenshot."))
            return render(request, 'core/checkout.html', {
                'cart_items': cart_items,
                'subtotal': subtotal,
                'full_name': full_name,
                'address': address,
                'phone_number': phone_number,
            })
            
        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            address=address,
            phone_number=phone_number,
            total_amount=subtotal,
            payment_screenshot=screenshot,
            status='AWAITING_VERIFICATION'
        )
        
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['price']
            )
            
        request.session['cart'] = {}
        request.session.modified = True
        
        messages.success(request, _t("Order submitted successfully! Awaiting owner confirmation."))
        return redirect('order_success', order_id=order.id)

    phone_number = getattr(request.user, 'phone_number', '') or ''
    return render(request, 'core/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'phone_number': phone_number,
    })


@login_required
def order_success_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.user != request.user and not request.user.is_owner:
        messages.error(request, _t("You do not have permission to view this order."))
        return redirect('store')
        
    return render(request, 'core/order_success.html', {'order': order})


def about_view(request):
    """
    Renders the About Us page with owner profiles and startup narrative.
    """
    return render(request, 'core/about.html')


