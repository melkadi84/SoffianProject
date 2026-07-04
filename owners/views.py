import csv
import io
import urllib.request
import tempfile
import os
import zipfile
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.core.files import File
from django.http import HttpResponse
from django.utils.text import slugify
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

    # Pop CSV import errors from session if present
    import_errors = request.session.pop('import_errors', None)

    return render(request, 'owners/product_list.html', {
        'products': products,
        'search': search,
        'import_errors': import_errors
    })


@owner_required
def product_export_template(request):
    """
    Exports a CSV template with header details and sample handcrafted items.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="product_import_template.csv"'

    writer = csv.writer(response)
    # Header
    writer.writerow(['name', 'category', 'description', 'price', 'status', 'rating', 'review_count', 'image_url'])
    # Sample Row 1
    writer.writerow([
        'Handmade Clay Mug',
        'Ceramics',
        'A beautifully crafted terracotta mug with a rustic glaze finish. Perfect for hot beverages.',
        '120.00',
        'PUBLISHED',
        '4.8',
        '15',
        'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?q=80&w=300'
    ])
    # Sample Row 2
    writer.writerow([
        'Embroidered Cushion Cover',
        'Textiles',
        'Colorful cotton cushion cover featuring traditional hand-stitched floral patterns.',
        '250.00',
        'DRAFT',
        '4.5',
        '8',
        ''
    ])
    return response


@owner_required
def product_import_csv(request):
    """
    Handles CSV parsing, validation, auto-category creation, optional image download,
    and bulk import inside an atomic transaction.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('owner_product_list')

    csv_file = request.FILES.get('csv_file')
    if not csv_file:
        messages.error(request, "Please upload a CSV file.")
        return redirect('owner_product_list')

    if not csv_file.name.endswith('.csv'):
        messages.error(request, "Uploaded file must be a CSV file.")
        return redirect('owner_product_list')

    try:
        # Read the file content
        file_data = csv_file.read().decode('utf-8-sig') # handling BOM
        csv_data = io.StringIO(file_data)
        reader = csv.DictReader(csv_data)
    except Exception as e:
        messages.error(request, f"Error reading CSV file: {str(e)}")
        return redirect('owner_product_list')

    # Check headers
    required_headers = {'name', 'category', 'description', 'price'}
    actual_headers = {h.strip().lower() for h in reader.fieldnames} if reader.fieldnames else set()
    missing_headers = required_headers - actual_headers
    if missing_headers:
        messages.error(request, f"CSV is missing required columns: {', '.join(missing_headers)}")
        return redirect('owner_product_list')

    errors = []
    products_to_create = [] # (product_obj, image_url_str) tuples

    # Start validation loop
    for row_idx, row in enumerate(reader, start=2): # 1-indexed row header is line 1, first data is line 2
        # Strip keys and values
        clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
        
        name = clean_row.get('name')
        category_name = clean_row.get('category')
        description = clean_row.get('description')
        price_str = clean_row.get('price')
        status = clean_row.get('status', 'DRAFT').upper()
        rating_str = clean_row.get('rating', '4.5')
        review_count_str = clean_row.get('review_count', '12')
        image_url = clean_row.get('image_url', '')

        row_errors = []

        # Validate name
        if not name:
            row_errors.append("Product name is required.")

        # Validate category
        if not category_name:
            row_errors.append("Category name is required.")

        # Validate description
        if not description:
            row_errors.append("Description is required.")

        # Validate price
        price = None
        if not price_str:
            row_errors.append("Price is required.")
        else:
            try:
                price = Decimal(price_str)
                if price <= 0:
                    row_errors.append("Price must be greater than zero.")
            except (InvalidOperation, ValueError):
                row_errors.append(f"Invalid price value: '{price_str}'. Must be a valid decimal number.")

        # Validate status
        if status not in ['DRAFT', 'PUBLISHED']:
            status = 'DRAFT' # safe default

        # Validate rating
        rating = 4.5
        if rating_str:
            try:
                rating = float(rating_str)
                if not (0.0 <= rating <= 5.0):
                    row_errors.append("Rating must be between 0.0 and 5.0.")
            except ValueError:
                row_errors.append(f"Invalid rating value: '{rating_str}'. Must be a number between 0.0 and 5.0.")

        # Validate review count
        review_count = 12
        if review_count_str:
            try:
                review_count = int(review_count_str)
                if review_count < 0:
                    row_errors.append("Review count cannot be negative.")
            except ValueError:
                row_errors.append(f"Invalid review count: '{review_count_str}'. Must be an integer.")

        if row_errors:
            errors.append(f"Row {row_idx}: " + "; ".join(row_errors))
            continue

        products_to_create.append({
            'name': name,
            'category_name': category_name,
            'description': description,
            'price': price,
            'status': status,
            'rating': rating,
            'review_count': review_count,
            'image_url': image_url,
            'row_idx': row_idx
        })

    # If any parsing/validation errors occurred, stop and roll back
    if errors:
        request.session['import_errors'] = errors
        messages.error(request, "CSV import failed due to validation errors. No products were imported.")
        return redirect('owner_product_list')

    # Proceed with database transactions
    imported_count = 0
    try:
        with transaction.atomic():
            for item in products_to_create:
                # 1. Resolve Category
                cat_name = item['category_name']
                # Case insensitive check
                category = Category.objects.filter(name__iexact=cat_name).first()
                if not category:
                    category = Category.objects.create(name=cat_name)

                # 2. Create Product (slug is auto-generated in model save method)
                prod = Product(
                    name=item['name'],
                    category=category,
                    description=item['description'],
                    price=item['price'],
                    status=item['status'],
                    rating=item['rating'],
                    review_count=item['review_count']
                )

                # Try image download if image_url is provided
                img_url = item['image_url']
                if img_url:
                    try:
                        img_temp = tempfile.TemporaryFile()
                        req = urllib.request.Request(
                            img_url,
                            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                        )
                        with urllib.request.urlopen(req, timeout=10) as response:
                            img_temp.write(response.read())
                        img_temp.seek(0)
                        filename = os.path.basename(img_url.split('?')[0])
                        if not filename or '.' not in filename:
                            filename = f"imported_product_{item['row_idx']}.jpg"
                        prod.image.save(filename, File(img_temp), save=False)
                    except Exception as img_err:
                        # We don't fail the import for image download errors, just let product save without image
                        pass

                prod.save()
                imported_count += 1
    except Exception as db_err:
        request.session['import_errors'] = [f"Database error during import: {str(db_err)}"]
        messages.error(request, "CSV import failed due to database error. No products were imported.")
        return redirect('owner_product_list')

    messages.success(request, f"Successfully imported {imported_count} products.")
    return redirect('owner_product_list')


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


@owner_required
def owner_database_backup_restore(request):
    """
    Renders the Backup & Restore dashboard.
    Handles backup generation (export ZIP of CSVs) and restore (import ZIP of CSVs).
    """
    from django.conf import settings
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile

    models_to_backup = [
        ('users', CustomUser),
        ('categories', Category),
        ('products', Product),
        ('product_images', ProductImage),
        ('themes', Theme),
        ('promotions', Promotion),
        ('orders', Order),
        ('order_items', OrderItem),
        ('app_configurations', AppConfiguration),
    ]

    if request.method == 'POST':
        action = request.POST.get('action')
        
        # --- EXPORT BACKUP ---
        if action == 'export':
            selected_categories = request.POST.getlist('categories')
            if not selected_categories:
                # Default to all categories + media if none specified (for backward compatibility / tests)
                selected_categories = [name for name, _ in models_to_backup] + ['media']
            try:
                # Create ZIP in-memory
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for filename, model_class in models_to_backup:
                        if filename in selected_categories:
                            # Generate CSV content for the model
                            csv_output = io.StringIO()
                            writer = csv.writer(csv_output)
                            
                            # Get all fields
                            fields = [f.name for f in model_class._meta.fields]
                            writer.writerow(fields)
                            
                            for obj in model_class.objects.all():
                                row = []
                                for field in fields:
                                    val = getattr(obj, field)
                                    if val is None:
                                        row.append('')
                                    elif isinstance(val, timezone.datetime):
                                        row.append(val.isoformat())
                                    else:
                                        row.append(str(val))
                                writer.writerow(row)
                            
                            zip_file.writestr(f"{filename}.csv", csv_output.getvalue())
                    
                    # Backup media if requested
                    if 'media' in selected_categories:
                        # 1. Walk settings.MEDIA_ROOT locally
                        if os.path.exists(settings.MEDIA_ROOT):
                            for root_dir, dirs, files in os.walk(settings.MEDIA_ROOT):
                                for file in files:
                                    local_path = os.path.join(root_dir, file)
                                    rel_path = os.path.relpath(local_path, settings.MEDIA_ROOT)
                                    zip_path = f"media/{rel_path.replace(os.sep, '/')}"
                                    try:
                                        with open(local_path, 'rb') as f:
                                            zip_file.writestr(zip_path, f.read())
                                    except Exception:
                                        pass

                        # 2. Walk default_storage referenced files (in case they are stored in Cloudinary/remote)
                        referenced_files = set()
                        try:
                            if 'products' in selected_categories:
                                for p in Product.objects.all():
                                    if p.image and p.image.name:
                                        referenced_files.add(p.image.name)
                            if 'product_images' in selected_categories:
                                for pi in ProductImage.objects.all():
                                    if pi.image and pi.image.name:
                                        referenced_files.add(pi.image.name)
                            if 'orders' in selected_categories:
                                for o in Order.objects.all():
                                    if o.payment_screenshot and o.payment_screenshot.name:
                                        referenced_files.add(o.payment_screenshot.name)
                        except Exception:
                            pass

                        for file_name in referenced_files:
                            zip_path = f"media/{file_name}"
                            if zip_path not in zip_file.namelist():
                                try:
                                    if default_storage.exists(file_name):
                                        with default_storage.open(file_name, 'rb') as f:
                                            zip_file.writestr(zip_path, f.read())
                                except Exception:
                                    pass
                
                zip_buffer.seek(0)
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="soffian_db_backup_{timestamp}.zip"'
                return response
            except Exception as e:
                messages.error(request, f"Error generating database backup: {str(e)}")
                return redirect('owner_database_backup_restore')
                
        # --- IMPORT/RESTORE BACKUP ---
        elif action == 'restore':
            selected_categories = request.POST.getlist('categories')
            if not selected_categories:
                # Default to all categories + media if none specified (for backward compatibility / tests)
                selected_categories = [name for name, _ in models_to_backup] + ['media']

            backup_file = request.FILES.get('backup_file')
            if not backup_file:
                messages.error(request, "Please upload a valid backup ZIP file.")
                return redirect('owner_database_backup_restore')
                
            if not backup_file.name.endswith('.zip'):
                messages.error(request, "Uploaded file must be a ZIP file.")
                return redirect('owner_database_backup_restore')
                
            try:
                # Read zip in-memory
                zip_data = io.BytesIO(backup_file.read())
                with zipfile.ZipFile(zip_data) as zip_file:
                    file_list = zip_file.namelist()
                    
                    # Read all CSV contents
                    csv_contents = {}
                    for name, _ in models_to_backup:
                        filename = f"{name}.csv"
                        if filename in file_list:
                            csv_contents[name] = zip_file.read(filename).decode('utf-8')
                    
                    # Validate that the selected DB categories actually exist in the zip file
                    for name in selected_categories:
                        if name != 'media':
                            filename = f"{name}.csv"
                            if filename not in file_list:
                                messages.error(request, f"Selected category '{name}' not found in the backup ZIP.")
                                return redirect('owner_database_backup_restore')
                    
                    # Perform restoration in transaction to ensure atomic rollback on failure
                    with transaction.atomic():
                        # Delete existing records of selected categories in reverse topological order
                        delete_order = [
                            ('order_items', OrderItem),
                            ('orders', Order),
                            ('promotions', Promotion),
                            ('product_images', ProductImage),
                            ('products', Product),
                            ('categories', Category),
                            ('users', CustomUser),
                            ('themes', Theme),
                            ('app_configurations', AppConfiguration),
                        ]
                        for name, model_class in delete_order:
                            if name in selected_categories:
                                model_class.objects.all().delete()
                        
                        # Restore in topological order
                        for name, model_class in models_to_backup:
                            if name in selected_categories and name in csv_contents:
                                reader = csv.DictReader(io.StringIO(csv_contents[name]))
                                for row in reader:
                                    data = {}
                                    for k, v in row.items():
                                        if not k:
                                            continue
                                        if v == '':
                                            data[k] = None
                                        else:
                                            data[k] = v
                                            
                                    obj = model_class(**data)
                                    obj.save()

                        # Restore media if selected
                        if 'media' in selected_categories:
                            zip_prefix = 'media/'
                            for zip_member in file_list:
                                if zip_member.startswith(zip_prefix) and zip_member != zip_prefix:
                                    storage_path = zip_member[len(zip_prefix):]
                                    if storage_path:
                                        file_content = zip_file.read(zip_member)
                                        if default_storage.exists(storage_path):
                                            try:
                                                default_storage.delete(storage_path)
                                            except Exception:
                                                pass
                                        default_storage.save(storage_path, ContentFile(file_content))
                                    
                messages.success(request, "Database has been successfully restored from backup.")
                return redirect('owner_database_backup_restore')
                
            except Exception as e:
                messages.error(request, f"Error restoring database: {str(e)}")
                return redirect('owner_database_backup_restore')

    return render(request, 'owners/database_backup_restore.html')


@owner_required
def owner_database_reset(request):
    """
    Renders the Reset Database dashboard.
    Clears catalog data when the owner type-confirms the reset action.
    """
    if request.method == 'POST':
        confirmation = request.POST.get('confirmation_phrase', '').strip()
        if confirmation != 'RESET DATABASE':
            messages.error(request, "Confirmation phrase did not match. Database reset canceled.")
            return redirect('owner_database_reset')

        try:
            with transaction.atomic():
                OrderItem.objects.all().delete()
                Order.objects.all().delete()
                Promotion.objects.all().delete()
                ProductImage.objects.all().delete()
                Product.objects.all().delete()
                Category.objects.all().delete()
                Theme.objects.all().delete()
                AppConfiguration.objects.all().delete()
                
            messages.success(request, "All catalog data has been successfully deleted. Database reset complete.")
            return redirect('owner_product_list')
        except Exception as e:
            messages.error(request, f"Error resetting database: {str(e)}")
            return redirect('owner_database_reset')

    return render(request, 'owners/database_reset.html')



