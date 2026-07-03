from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum
from django import forms
from functools import wraps
from core.models import Product, Category, Promotion, CustomUser, Order, OrderItem, Theme, ProductImage, AppConfiguration
from core.translations import _t

# Security decorator for Owner-only access
def owner_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in first.")
            return redirect('login')
        if not (request.user.is_owner or request.user.is_staff or request.user.is_superuser):
            messages.warning(request, "Access denied. You do not have owner portal privileges.")
            return redirect('store')
        return view_func(request, *args, **kwargs)
    return wrapper

# Forms definitions
class ProductForm(forms.ModelForm):
    is_published = forms.BooleanField(
        required=False,
        label="Published Status",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch', 'id': 'status-toggle'})
    )

    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'image', 'rating', 'review_count']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Rustic Ceramic Tea Pot'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the handcraft details...'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.0', 'max': '5.0', 'placeholder': '4.5'}),
            'review_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '12'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial['rating'] = 4.5
            self.initial['review_count'] = 12
            self.initial['is_published'] = False
        else:
            self.initial['is_published'] = (self.instance.status == 'PUBLISHED')

    def save(self, commit=True):
        product = super().save(commit=False)
        if self.cleaned_data.get('is_published'):
            product.status = 'PUBLISHED'
        else:
            product.status = 'DRAFT'
        if commit:
            product.save()
        return product


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Ceramics & Pottery'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., bi-bezier2'}),
        }


class AppConfigurationForm(forms.ModelForm):
    class Meta:
        model = AppConfiguration
        fields = [
            'artisan_promise_title_en', 'artisan_promise_title_ar',
            'artisan_promise_text_en', 'artisan_promise_text_ar',
            'footer_description_en', 'footer_description_ar',
            'free_delivery_title_en', 'free_delivery_title_ar',
            'free_delivery_subtitle_en', 'free_delivery_subtitle_ar',
            'secure_checkout_title_en', 'secure_checkout_title_ar',
            'secure_checkout_subtitle_en', 'secure_checkout_subtitle_ar',
            'empty_cart_title_en', 'empty_cart_title_ar',
            'empty_cart_text_en', 'empty_cart_text_ar',
            'founder1_name_en', 'founder1_name_ar',
            'founder1_role_en', 'founder1_role_ar',
            'founder1_bio_en', 'founder1_bio_ar',
            'founder2_name_en', 'founder2_name_ar',
            'founder2_role_en', 'founder2_role_ar',
            'founder2_bio_en', 'founder2_bio_ar',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'bio' in field_name or 'text' in field_name or 'description' in field_name:
                field.widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
            else:
                field.widget = forms.TextInput(attrs={'class': 'form-control'})



class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ['name', 'discount_type', 'discount_value', 'scope', 'category', 'product', 'start_date', 'end_date', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Winter Holiday Discount'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g., 20.00'}),
            'scope': forms.Select(attrs={'class': 'form-select', 'id': 'promo-scope-select'}),
            'category': forms.Select(attrs={'class': 'form-select', 'id': 'promo-category-select'}),
            'product': forms.Select(attrs={'class': 'form-select', 'id': 'promo-product-select'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Format datetime strings for HTML5 datetime-local widget when editing
        if self.instance.pk:
            if self.instance.start_date:
                self.initial['start_date'] = self.instance.start_date.strftime('%Y-%m-%dT%H:%M')
            if self.instance.end_date:
                self.initial['end_date'] = self.instance.end_date.strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        scope = cleaned_data.get('scope')
        category = cleaned_data.get('category')
        product = cleaned_data.get('product')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Scope validation checks
        if scope == 'CATEGORY' and not category:
            self.add_error('category', 'Please select a target Category for this promotion.')
        if scope == 'PRODUCT' and not product:
            self.add_error('product', 'Please select a target Product for this promotion.')
            
        # Date boundary validation checks
        if start_date and end_date and start_date >= end_date:
            self.add_error('end_date', 'End date must be strictly after the start date.')
            
        return cleaned_data


# View handlers
@owner_required
def owner_dashboard(request):
    """
    Renders analytics totals and quick lists.
    """
    total_products = Product.objects.count()
    published_products = Product.objects.filter(status='PUBLISHED').count()
    draft_products = Product.objects.filter(status='DRAFT').count()
    categories_count = Category.objects.count()
    
    now = timezone.now()
    active_promotions_count = Promotion.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).count()

    # Instapay orders metrics
    pending_orders_count = Order.objects.filter(status='AWAITING_VERIFICATION').count()
    sales_aggregation = Order.objects.filter(status__in=['CONFIRMED', 'SHIPPED']).aggregate(total=Sum('total_amount'))
    total_sales = sales_aggregation['total'] or 0

    recent_products = Product.objects.all().order_by('-created_at')[:5]
    recent_promotions = Promotion.objects.all().order_by('-created_at')[:5]
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    categories_with_counts = Category.objects.annotate(product_count=Count('products')).order_by('-product_count')

    context = {
        'total_products': total_products,
        'published_products': published_products,
        'draft_products': draft_products,
        'categories_count': categories_count,
        'active_promotions_count': active_promotions_count,
        'pending_orders_count': pending_orders_count,
        'total_sales': total_sales,
        'recent_products': recent_products,
        'recent_promotions': recent_promotions,
        'recent_orders': recent_orders,
        'categories_with_counts': categories_with_counts,
        'now': now,
    }
    return render(request, 'owners/dashboard.html', context)


@owner_required
def product_list(request):
    """
    Renders a paginated table of products.
    """
    products = Product.objects.all().order_by('-created_at')
    
    # Search within list
    search = request.GET.get('search')
    if search:
        products = products.filter(name__icontains=search)

    return render(request, 'owners/product_list.html', {'products': products, 'search': search})


@owner_required
def product_create_or_edit(request, pk=None):
    """
    Form view for adding or editing a product, showcasing split screen live preview.
    """
    product = get_object_or_404(Product, pk=pk) if pk else None
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        
        uploaded_images = request.FILES.getlist('images')
        delete_image_ids = request.POST.getlist('delete_image_ids')
        
        # Calculate final image count
        existing_extra_count = product.images.count() if product else 0
        deleted_count = 0
        if delete_image_ids and product:
            deleted_count = product.images.filter(id__in=delete_image_ids).count()
            
        has_primary = False
        if request.FILES.get('image'):
            has_primary = True
        elif product and product.image and not request.POST.get('image-clear'):
            has_primary = True
            
        total_after_changes = (1 if has_primary else 0) + (existing_extra_count - deleted_count) + len(uploaded_images)
        
        if total_after_changes > 5:
            form.add_error(None, "Total pictures cannot exceed 5. Please remove some photos or upload fewer.")
            messages.error(request, "Total pictures cannot exceed 5. Please check your image selections.")
        elif form.is_valid():
            saved_product = form.save()
            
            # Deletions of extra images
            if delete_image_ids:
                ProductImage.objects.filter(id__in=delete_image_ids, product=saved_product).delete()
                
            # Save new extra images
            for img_file in uploaded_images:
                ProductImage.objects.create(product=saved_product, image=img_file)
                
            verb = 'updated' if product else 'published'
            messages.success(request, f'Product "{saved_product.name}" has been successfully {verb}!')
            return redirect('owner_product_list')
        else:
            messages.error(request, "There was an error saving the product. Please check the inputs.")
    else:
        form = ProductForm(instance=product)

    context = {
        'form': form,
        'product': product,
        'categories': Category.objects.all(),
        'is_edit': bool(product)
    }
    return render(request, 'owners/product_form.html', context)


@owner_required
def product_delete(request, pk):
    """
    Deletes product from inventory.
    """
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()
    messages.success(request, f'Product "{name}" has been deleted.')
    return redirect('owner_product_list')


@owner_required
def promotion_list(request):
    """
    List view for all sales and discounts.
    """
    promotions = Promotion.objects.all().order_by('-created_at')
    now = timezone.now()
    return render(request, 'owners/promotion_list.html', {'promotions': promotions, 'now': now})


@owner_required
def promotion_create_or_edit(request, pk=None):
    """
    Form view for adding or scheduling discounts.
    """
    promotion = get_object_or_404(Promotion, pk=pk) if pk else None
    
    if request.method == 'POST':
        form = PromotionForm(request.POST, instance=promotion)
        if form.is_valid():
            saved_promo = form.save()
            verb = 'updated' if promotion else 'created'
            messages.success(request, f'Promotion "{saved_promo.name}" has been successfully {verb}!')
            return redirect('owner_promotion_list')
        else:
            messages.error(request, "There was an error saving the promotion. Please check values.")
    else:
        form = PromotionForm(instance=promotion)

    context = {
        'form': form,
        'promotion': promotion,
        'is_edit': bool(promotion)
    }
    return render(request, 'owners/promotion_form.html', context)


@owner_required
def promotion_delete(request, pk):
    """
    Deletes promotion campaign.
    """
    promotion = get_object_or_404(Promotion, pk=pk)
    name = promotion.name
    promotion.delete()
    messages.success(request, f'Promotion "{name}" has been deleted.')
    return redirect('owner_promotion_list')


@owner_required
def category_list(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'owners/category_list.html', {'categories': categories})


@owner_required
def category_create_or_edit(request, pk=None):
    category = get_object_or_404(Category, pk=pk) if pk else None
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            saved_cat = form.save()
            verb = 'updated' if category else 'created'
            messages.success(request, f'Category "{saved_cat.name}" has been successfully {verb}!')
            return redirect('owner_category_list')
        else:
            messages.error(request, "There was an error saving the category. Please check inputs.")
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'owners/category_form.html', {
        'form': form,
        'category': category,
        'is_edit': bool(category)
    })


@owner_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    name = category.name
    
    product_count = category.products.count()
    if product_count > 0:
        messages.error(request, f'Cannot delete category "{name}". It has {product_count} products assigned. Reassign or delete those products first!')
        return redirect('owner_category_list')
        
    category.delete()
    messages.success(request, f'Category "{name}" has been deleted successfully.')
    return redirect('owner_category_list')


@owner_required
def theme_list(request):
    # Self-healing database seeding for the 10 portals
    if Theme.objects.count() == 0:
        themes = [
            {
                'name': 'Little Creators Shop Classic',
                'primary_color': '#8c6239',
                'primary_hover_color': '#6e4c2b',
                'bg_color': '#f9f6f0',
                'dark_color': '#221a15',
                'primary_light_color': '#f5ede4',
                'border_color': '#e6dfd5',
                'is_active': True,
            },
            {
                'name': 'Amazon Amber',
                'primary_color': '#ff9900',
                'primary_hover_color': '#df8600',
                'bg_color': '#eaeded',
                'dark_color': '#131921',
                'primary_light_color': '#f3f3f3',
                'border_color': '#d5dbdb',
                'is_active': False,
            },
            {
                'name': 'Etsy Tangerine',
                'primary_color': '#f1641e',
                'primary_hover_color': '#d04e10',
                'bg_color': '#fcfbfa',
                'dark_color': '#222222',
                'primary_light_color': '#fdeee6',
                'border_color': '#e7e7e7',
                'is_active': False,
            },
            {
                'name': 'Shopify Premium',
                'primary_color': '#008060',
                'primary_hover_color': '#006048',
                'bg_color': '#f6f6f7',
                'dark_color': '#1a1a1a',
                'primary_light_color': '#e3f1ed',
                'border_color': '#e1e3e5',
                'is_active': False,
            },
            {
                'name': 'eBay Bright',
                'primary_color': '#0063d1',
                'primary_hover_color': '#004b9e',
                'bg_color': '#f7f7f7',
                'dark_color': '#191919',
                'primary_light_color': '#e5f0fa',
                'border_color': '#dddddd',
                'is_active': False,
            },
            {
                'name': 'IKEA Bright Blue',
                'primary_color': '#0058ab',
                'primary_hover_color': '#00407c',
                'bg_color': '#ffffff',
                'dark_color': '#111111',
                'primary_light_color': '#ffdb00',
                'border_color': '#e5e5e5',
                'is_active': False,
            },
            {
                'name': 'Apple Minimalist',
                'primary_color': '#000000',
                'primary_hover_color': '#333333',
                'bg_color': '#f5f5f7',
                'dark_color': '#1d1d1f',
                'primary_light_color': '#e8e8ed',
                'border_color': '#d2d2d7',
                'is_active': False,
            },
            {
                'name': 'Netflix Dark Crimson',
                'primary_color': '#e50914',
                'primary_hover_color': '#b80710',
                'bg_color': '#141414',
                'dark_color': '#000000',
                'primary_light_color': '#2f0204',
                'border_color': '#333333',
                'is_active': False,
            },
            {
                'name': 'GitHub Slate',
                'primary_color': '#0969da',
                'primary_hover_color': '#0550ae',
                'bg_color': '#f6f8fa',
                'dark_color': '#24292f',
                'primary_light_color': '#ddf4ff',
                'border_color': '#d0d7de',
                'is_active': False,
            },
            {
                'name': 'Target Energetic Red',
                'primary_color': '#cc0000',
                'primary_hover_color': '#990000',
                'bg_color': '#f7f7f7',
                'dark_color': '#333333',
                'primary_light_color': '#fcebeb',
                'border_color': '#e1e1e1',
                'is_active': False,
            }
        ]
        for t in themes:
            Theme.objects.create(**t)
            
    themes = Theme.objects.all().order_by('id')
    active_theme = Theme.objects.filter(is_active=True).first()
    return render(request, 'owners/theme_list.html', {
        'themes': themes,
        'active_theme': active_theme,
        'font_choices_en': Theme.FONT_CHOICES_EN,
        'font_choices_ar': Theme.FONT_CHOICES_AR,
    })


@owner_required
def theme_activate(request, pk):
    theme = get_object_or_404(Theme, pk=pk)
    theme.is_active = True
    theme.save()
    messages.success(request, _t('Theme "{}" activated successfully across all portals!', theme.name))
    return redirect('owner_theme_list')


@owner_required
def theme_change_font(request):
    """
    Action endpoint to change the English and Arabic font of the active theme.
    """
    if request.method == 'POST':
        font_family_en = request.POST.get('font_family_en')
        font_family_ar = request.POST.get('font_family_ar')
        active_theme = Theme.objects.filter(is_active=True).first()
        if active_theme:
            if font_family_en:
                active_theme.font_family_en = font_family_en
            if font_family_ar:
                active_theme.font_family_ar = font_family_ar
            active_theme.save()
            messages.success(request, _t("Font preferences updated successfully."))
        else:
            messages.error(request, _t("No active theme found."))
    return redirect('owner_theme_list')


@owner_required
def order_list(request):
    """
    Renders list of all customer orders.
    """
    orders = Order.objects.all().order_by('-created_at')
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'owners/order_list.html', {
        'orders': orders,
        'status_filter': status_filter
    })


@owner_required
def order_detail(request, pk):
    """
    Shows detail of a specific order, payment screenshot, and verification options.
    """
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'owners/order_detail.html', {
        'order': order
    })


@owner_required
def order_update_status(request, pk, status):
    """
    Action endpoint to approve/reject/ship orders.
    """
    order = get_object_or_404(Order, pk=pk)
    if status not in ['CONFIRMED', 'SHIPPED', 'CANCELLED']:
        messages.error(request, _t("Invalid status choice."))
        return redirect('owner_order_detail', pk=order.id)
    order.status = status
    order.save()
    messages.success(request, _t("Order status updated successfully."))
    return redirect('owner_order_detail', pk=order.id)


@owner_required
def order_bulk_delete(request):
    """
    Action endpoint to delete multiple orders at once.
    """
    if request.method == 'POST':
        order_ids = request.POST.getlist('order_ids')
        if order_ids:
            deleted_count, _ = Order.objects.filter(id__in=order_ids).delete()
            messages.success(request, f'Successfully deleted {deleted_count} order(s).')
        else:
            messages.warning(request, 'No orders were selected for deletion.')
    return redirect('owner_order_list')


@owner_required
def app_configuration_edit(request):
    config = AppConfiguration.get_solo()
    if request.method == 'POST':
        form = AppConfigurationForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Application configurations updated successfully.")
            return redirect('owner_app_configuration')
    else:
        form = AppConfigurationForm(instance=config)
        
    return render(request, 'owners/app_configuration.html', {'form': form, 'config': config})


from django.views.decorators.http import require_POST
from django.http import JsonResponse

@owner_required
@require_POST
def ajax_category_create(request):
    """
    AJAX endpoint for creating a new Category on-the-fly.
    """
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'success': False, 'error': 'Category name is required.'}, status=400)
        
    if Category.objects.filter(name__iexact=name).exists():
        return JsonResponse({'success': False, 'error': 'A category with this name already exists.'}, status=400)
        
    try:
        category = Category.objects.create(name=name)
        return JsonResponse({
            'success': True,
            'id': category.id,
            'name': category.name
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



