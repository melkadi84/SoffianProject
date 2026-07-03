from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.utils import timezone
from decimal import Decimal

class CustomUser(AbstractUser):
    AUTH_PROVIDER_CHOICES = (
        ('EMAIL', 'Email'),
        ('GOOGLE', 'Google'),
        ('APPLE', 'Apple'),
        ('MOBILE', 'Mobile'),
    )
    
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    auth_provider = models.CharField(max_length=10, choices=AUTH_PROVIDER_CHOICES, default='EMAIL')
    is_owner = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    icon = models.CharField(max_length=50, default='bi-box-seam', help_text="Bootstrap Icon class name")

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
    )

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2) # wait, max_digits=10, decimal_places=2 is the correct django parameter name. Let's make sure.
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate a slug, append id if duplicate
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def active_promotion_info(self):
        """
        Returns a dict with {'promotion': promo_obj, 'discounted_price': price}
        if there is an active promotion, else None.
        """
        now = timezone.now()
        
        # Query active promotions in duration
        promos = Promotion.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )
        
        applicable_promos = []
        for p in promos:
            if p.scope == 'PRODUCT' and p.product_id == self.id:
                applicable_promos.append(p)
            elif p.scope == 'CATEGORY' and p.category_id == self.category_id:
                applicable_promos.append(p)
            elif p.scope == 'ALL':
                applicable_promos.append(p)
                
        if not applicable_promos:
            return None
            
        best_promo = None
        lowest_price = self.price
        
        for p in applicable_promos:
            discounted = p.calculate_discount(self.price)
            if discounted < lowest_price:
                lowest_price = discounted
                best_promo = p
                
        if best_promo:
            return {
                'promotion': best_promo,
                'discounted_price': lowest_price
            }
        return None

    @property
    def active_price(self):
        info = self.active_promotion_info
        if info:
            return info['discounted_price']
        return self.price

    @property
    def is_on_sale(self):
        return self.active_promotion_info is not None

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name} ({self.id})"


class Promotion(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('PERCENTAGE', 'Percentage Discount'),
        ('FIXED_AMOUNT', 'Fixed Amount Discount'),
        ('SPECIAL_PRICE', 'Special Price Overwrite'),
    )
    
    SCOPE_CHOICES = (
        ('ALL', 'All Products'),
        ('CATEGORY', 'Per Category'),
        ('PRODUCT', 'Single Product'),
    )

    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True, related_name='promotions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True, related_name='promotions')
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_discount(self, original_price):
        if self.discount_type == 'PERCENTAGE':
            discount_amount = original_price * (self.discount_value / Decimal('100.0'))
            return max(original_price - discount_amount, Decimal('0.00'))
        elif self.discount_type == 'FIXED_AMOUNT':
            return max(original_price - self.discount_value, Decimal('0.00'))
        elif self.discount_type == 'SPECIAL_PRICE':
            return max(self.discount_value, Decimal('0.00'))
        return original_price

    def __str__(self):
        return f"{self.name} ({self.get_scope_display()})"


class Theme(models.Model):
    FONT_CHOICES_EN = (
        ("'Inter', sans-serif", "Inter (Clean & Modern)"),
        ("'Outfit', sans-serif", "Outfit (Geometric & Premium)"),
        ("'Roboto', sans-serif", "Roboto (Standard Sans)"),
        ("'Playfair Display', serif", "Playfair (Classic Serif)"),
    )
    FONT_CHOICES_AR = (
        ("'Cairo', sans-serif", "Cairo (Modern & Rounded)"),
        ("'Tajawal', sans-serif", "Tajawal (Sleek Kufic)"),
        ("'Almarai', sans-serif", "Almarai (Corporate Clean)"),
        ("'Amiri', serif", "Amiri (Traditional Naskh)"),
    )

    name = models.CharField(max_length=50, unique=True)
    primary_color = models.CharField(max_length=7) # Hex e.g., #ff9900
    primary_hover_color = models.CharField(max_length=7)
    bg_color = models.CharField(max_length=7)
    dark_color = models.CharField(max_length=7)
    primary_light_color = models.CharField(max_length=7)
    border_color = models.CharField(max_length=7)
    font_family_en = models.CharField(max_length=100, choices=FONT_CHOICES_EN, default="'Inter', sans-serif")
    font_family_ar = models.CharField(max_length=100, choices=FONT_CHOICES_AR, default="'Cairo', sans-serif")
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_active:
            Theme.objects.exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = (
        ('AWAITING_VERIFICATION', 'Awaiting Verification'),
        ('CONFIRMED', 'Confirmed / Paid'),
        ('SHIPPED', 'Shipped'),
        ('CANCELLED', 'Cancelled'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('INSTAPAY', 'Instapay Transfer'),
        ('COD', 'Cash on Delivery (COD)'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    full_name = models.CharField(max_length=150)
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='INSTAPAY')
    payment_screenshot = models.ImageField(upload_to='screenshots/', blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='AWAITING_VERIFICATION')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Price at checkout

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.order.id})"


from django.utils.translation import get_language

class AppConfiguration(models.Model):
    # Artisan Promise
    artisan_promise_title_en = models.CharField(max_length=200, default="Artisan Promise")
    artisan_promise_title_ar = models.CharField(max_length=200, default="عهد الحرفيين")
    artisan_promise_text_en = models.TextField(default="Every product listed is verified 100% handmade and unique.")
    artisan_promise_text_ar = models.TextField(default="كل منتج معروض هنا مضمون أنه مصنوع يدوياً 100% وفريد من نوعه.")
    
    footer_description_en = models.TextField(default="A premium marketplace dedicated to authentic handcrafts, wooden carvings, rustic pottery, and artisan masterpieces. Bringing human touch back into shopping.")
    footer_description_ar = models.TextField(default="منصة متميزة مخصصة للمشغولات اليدوية الأصيلة، والمنحوتات الخشبية، والفخار الريفي، والقطع الفنية الفريدة. نعيد اللمسة الإنسانية إلى التسوق.")

    # Delivery & Checkout
    free_delivery_title_en = models.CharField(max_length=200, default="Free Delivery")
    free_delivery_title_ar = models.CharField(max_length=200, default="شحن مجاني")
    free_delivery_subtitle_en = models.CharField(max_length=200, default="Orders over EGP 500")
    free_delivery_subtitle_ar = models.CharField(max_length=200, default="للطلبات فوق 500 ج.م")
    
    secure_checkout_title_en = models.CharField(max_length=200, default="Secure Checkout")
    secure_checkout_title_ar = models.CharField(max_length=200, default="دفع آمن")
    secure_checkout_subtitle_en = models.CharField(max_length=200, default="SSL Secured payments")
    secure_checkout_subtitle_ar = models.CharField(max_length=200, default="مدفوعات مؤمنة بـ SSL")

    # Cart
    empty_cart_title_en = models.CharField(max_length=200, default="Your Cart is Empty")
    empty_cart_title_ar = models.CharField(max_length=200, default="سلة التسوق فارغة")
    empty_cart_text_en = models.TextField(default="Discover authentic wooden carvings, rustic pottery, and hand-woven masterpieces. Add them to your cart to checkout!")
    empty_cart_text_ar = models.TextField(default="اكتشف المنحوتات الخشبية الأصيلة، والفخار الريفي، والتحف المنسوجة يدوياً. أضفها إلى سلتك لإتمام الشراء!")

    # Founders
    founder1_name_en = models.CharField(max_length=200, default="Soffian Elkadi")
    founder1_name_ar = models.CharField(max_length=200, default="سفيان القاضي")
    founder1_role_en = models.CharField(max_length=200, default="Co-Founder & Lead Designer")
    founder1_role_ar = models.CharField(max_length=200, default="شريك مؤسس ومصمم رئيسي")
    founder1_bio_en = models.TextField(default="Soffian is an award-winning ceramicist and digital designer with over a decade of experience styling premium homeware. He steers the visual identity and product quality assurance at Little Creators Shop.")
    founder1_bio_ar = models.TextField(default="سفيان هو خبير فخار ومصمم رقمي حائز على جوائز، يتمتع بخبرة تزيد عن عقد في تصميم الأدوات المنزلية الفاخرة. يقود الهوية البصرية وضمان جودة المنتجات في Little Creators Shop.")

    founder2_name_en = models.CharField(max_length=200, default="Yehia Fatouh")
    founder2_name_ar = models.CharField(max_length=200, default="يحيى فتوح")
    founder2_role_en = models.CharField(max_length=200, default="Co-Founder & Operations Head")
    founder2_role_ar = models.CharField(max_length=200, default="شريك مؤسس ومدير العمليات")
    founder2_bio_en = models.TextField(default="Yehia brings years of supply-chain and logistics management experience in regional craft trade. He supervises our onboarding pipelines, logistics partnerships, and verification guidelines.")
    founder2_bio_ar = models.TextField(default="يحيى يجلب سنوات من الخبرة في إدارة العمليات وسلاسل الإمداد اللوجستية في تجارة الحرف اليدوية الإقليمية. ويشرف على خطوط الإمداد والشراكات اللوجستية وإرشادات التحقق.")

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj

    def _get_field_by_lang(self, field_base):
        lang = get_language() or 'en'
        lang_short = lang.split('-')[0].lower()
        attr_name = f"{field_base}_{lang_short}"
        if hasattr(self, attr_name):
            return getattr(self, attr_name)
        return getattr(self, f"{field_base}_en")

    @property
    def artisan_promise_title(self):
        return self._get_field_by_lang('artisan_promise_title')

    @property
    def artisan_promise_text(self):
        return self._get_field_by_lang('artisan_promise_text')

    @property
    def footer_description(self):
        return self._get_field_by_lang('footer_description')

    @property
    def free_delivery_title(self):
        return self._get_field_by_lang('free_delivery_title')

    @property
    def free_delivery_subtitle(self):
        return self._get_field_by_lang('free_delivery_subtitle')

    @property
    def secure_checkout_title(self):
        return self._get_field_by_lang('secure_checkout_title')

    @property
    def secure_checkout_subtitle(self):
        return self._get_field_by_lang('secure_checkout_subtitle')

    @property
    def empty_cart_title(self):
        return self._get_field_by_lang('empty_cart_title')

    @property
    def empty_cart_text(self):
        return self._get_field_by_lang('empty_cart_text')

    @property
    def founder1_name(self):
        return self._get_field_by_lang('founder1_name')

    @property
    def founder1_role(self):
        return self._get_field_by_lang('founder1_role')

    @property
    def founder1_bio(self):
        return self._get_field_by_lang('founder1_bio')

    @property
    def founder2_name(self):
        return self._get_field_by_lang('founder2_name')

    @property
    def founder2_role(self):
        return self._get_field_by_lang('founder2_role')

    @property
    def founder2_bio(self):
        return self._get_field_by_lang('founder2_bio')

    def __str__(self):
        return "Application Configuration"


