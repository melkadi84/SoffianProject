from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from core.models import CustomUser, Category, Product, Promotion

class CraftsTestCase(TestCase):
    def setUp(self):
        # Create Category
        self.category = Category.objects.create(name="Woodwork", icon="bi-tree")
        self.other_category = Category.objects.create(name="Ceramics", icon="bi-bezier")
        
        # Create Products
        self.product = Product.objects.create(
            name="Wooden Spoon",
            category=self.category,
            description="Handmade spoon",
            price=Decimal("20.00"),
            status="PUBLISHED"
        )
        
        self.draft_product = Product.objects.create(
            name="Wooden Fork",
            category=self.category,
            description="Handmade fork in progress",
            price=Decimal("15.00"),
            status="DRAFT"
        )
        
        # Create Users
        self.normal_user = CustomUser.objects.create_user(
            username="normaluser",
            email="normal@crafts.com",
            password="password123",
            is_owner=False,
            email_verified=True
        )
        
        self.owner_user = CustomUser.objects.create_user(
            username="owneruser",
            email="owner@crafts.com",
            password="password123",
            is_owner=True,
            email_verified=True
        )
        
        self.client = Client()

    def test_promotion_precedence_and_calculation(self):
        """
        Verify that the product calculates the lowest price when multiple promotions apply.
        """
        now = timezone.now()
        future = now + timedelta(days=5)
        
        # Initially, no promotions, active_price should equal base price
        self.assertEqual(self.product.active_price, Decimal("20.00"))
        self.assertFalse(self.product.is_on_sale)

        # 1. Add a Global Promotion of $2 off (scope=ALL)
        global_promo = Promotion.objects.create(
            name="Welcome sale",
            discount_type="FIXED_AMOUNT",
            discount_value=Decimal("2.00"),
            scope="ALL",
            start_date=now - timedelta(hours=1),
            end_date=future,
            is_active=True
        )
        # Price should be 20.00 - 2.00 = 18.00
        self.assertEqual(self.product.active_price, Decimal("18.00"))
        self.assertTrue(self.product.is_on_sale)

        # 2. Add a Category Promotion of 20% off (Woodwork category).
        # 20.00 - 20% = 16.00. This is lower than $18.00 global, so it should take precedence.
        cat_promo = Promotion.objects.create(
            name="Woodwork discount",
            discount_type="PERCENTAGE",
            discount_value=Decimal("20.00"),
            scope="CATEGORY",
            category=self.category,
            start_date=now - timedelta(hours=1),
            end_date=future,
            is_active=True
        )
        self.assertEqual(self.product.active_price, Decimal("16.00"))

        # 3. Add a Product Promotion of special price $12.00
        # $12.00 is lower than $16.00 category discount, so it should take precedence.
        prod_promo = Promotion.objects.create(
            name="Spoon special price",
            discount_type="SPECIAL_PRICE",
            discount_value=Decimal("12.00"),
            scope="PRODUCT",
            product=self.product,
            start_date=now - timedelta(hours=1),
            end_date=future,
            is_active=True
        )
        self.assertEqual(self.product.active_price, Decimal("12.00"))

    def test_draft_product_storefront_visibility(self):
        """
        Verify that draft products are not visible to normal users, but are to owners.
        """
        # Storefront listing should show published product, but not draft product
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertNotContains(response, self.draft_product.name)

        # Detail view for draft product should return 404 for anonymous/normal user
        response = self.client.get(f'/product/{self.draft_product.slug}/')
        self.assertEqual(response.status_code, 404)

        # Detail view for draft product should return 200 for logged-in owner
        self.client.login(email="owner@crafts.com", password="password123")
        response = self.client.get(f'/product/{self.draft_product.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.draft_product.name)

    def test_owner_dashboard_permission_protection(self):
        """
        Verify that only users with owner/staff flag can access /owners pages.
        """
        # Anonymous user: redirected to login
        response = self.client.get('/owners/')
        self.assertRedirects(response, '/login/')

        # Logged-in normal user: redirected back to storefront with error warning
        self.client.login(email="normal@crafts.com", password="password123")
        response = self.client.get('/owners/', follow=True)
        self.assertRedirects(response, '/')
        self.assertContains(response, "Access denied")

        # Logged-in owner user: successfully displays dashboard
        self.client.logout()
        self.client.login(email="owner@crafts.com", password="password123")
        response = self.client.get('/owners/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_theme_activation_override(self):
        """
        Verify that activating one theme deactivates all other themes,
        and that the context processor correctly exposes the active theme.
        """
        from core.models import Theme
        from core.context_processors import theme_processor

        # Create two themes
        theme1 = Theme.objects.create(
            name="Theme One",
            primary_color="#111111",
            primary_hover_color="#222222",
            bg_color="#333333",
            dark_color="#444444",
            primary_light_color="#555555",
            border_color="#666666",
            is_active=True
        )
        
        theme2 = Theme.objects.create(
            name="Theme Two",
            primary_color="#aaaaaa",
            primary_hover_color="#bbbbbb",
            bg_color="#cccccc",
            dark_color="#dddddd",
            primary_light_color="#eeeeee",
            border_color="#ffffff",
            is_active=False
        )

        self.assertTrue(Theme.objects.get(id=theme1.id).is_active)
        self.assertFalse(Theme.objects.get(id=theme2.id).is_active)

        # Activate Theme Two
        theme2.is_active = True
        theme2.save()

        # Check that Theme One is automatically deactivated
        self.assertFalse(Theme.objects.get(id=theme1.id).is_active)
        self.assertTrue(Theme.objects.get(id=theme2.id).is_active)

        # Check context processor outcome
        context = theme_processor(None)
        self.assertEqual(context['theme'].name, "Theme Two")
        self.assertEqual(context['theme'].primary_color, "#aaaaaa")

    def test_cart_operations(self):
        """
        Verify that adding, adjusting quantities, and removing products in session cart works.
        """
        # 1. Add Wooden Spoon to cart
        response = self.client.get(f'/cart/add/{self.product.id}/?quantity=2')
        self.assertRedirects(response, '/cart/')
        
        # Verify quantity in session
        session = self.client.session
        self.assertIn(str(self.product.id), session['cart'])
        self.assertEqual(session['cart'][str(self.product.id)], 2)
        
        # 2. Decrement by 1 (sending -1)
        response = self.client.get(f'/cart/add/{self.product.id}/?quantity=-1')
        session = self.client.session
        self.assertEqual(session['cart'][str(self.product.id)], 1)
        
        # 3. Decrement to 0 (sending -1 again, should remove item)
        response = self.client.get(f'/cart/add/{self.product.id}/?quantity=-1')
        session = self.client.session
        self.assertNotIn(str(self.product.id), session.get('cart', {}))
        
        # 4. Add again and remove completely
        self.client.get(f'/cart/add/{self.product.id}/?quantity=3')
        response = self.client.get(f'/cart/remove/{self.product.id}/')
        self.assertRedirects(response, '/cart/')
        session = self.client.session
        self.assertNotIn(str(self.product.id), session.get('cart', {}))

    def test_checkout_and_order_creation(self):
        """
        Verify that users can submit Instapay checkout forms with screenshots
        to create DB orders and clear the cart.
        """
        from django.core.files.uploadedfile import SimpleUploadedFile
        from core.models import Order, OrderItem
        
        # Add item to cart and login
        self.client.get(f'/cart/add/{self.product.id}/?quantity=2')
        self.client.login(email="normal@crafts.com", password="password123")
        
        # Mock payment screenshot image
        mock_screenshot = SimpleUploadedFile(
            name='screenshot.png',
            content=b'mock_image_binary_content_here',
            content_type='image/png'
        )
        
        # Post checkout form
        post_data = {
            'full_name': 'Jane Doe',
            'phone_number': '01122334455',
            'address': 'Cairo, Egypt',
            'payment_screenshot': mock_screenshot
        }
        response = self.client.post('/checkout/', post_data)
        
        # Verify order created in DB
        order = Order.objects.filter(user=self.normal_user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.full_name, 'Jane Doe')
        self.assertEqual(order.total_amount, Decimal('40.00')) # 20.00 * 2
        self.assertEqual(order.status, 'AWAITING_VERIFICATION')
        
        # Verify order items
        order_item = OrderItem.objects.filter(order=order).first()
        self.assertIsNotNone(order_item)
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 2)
        
        # Verify cart was cleared
        session = self.client.session
        self.assertEqual(session.get('cart'), {})
        
        # Verify redirection to success page
        self.assertRedirects(response, f'/order/success/{order.id}/')

    def test_checkout_cod_order_creation(self):
        """
        Verify that users can submit Cash on Delivery (COD) checkout forms
        WITHOUT providing a payment screenshot to create DB orders and clear the cart.
        """
        from core.models import Order, OrderItem
        
        # Add item to cart and login
        self.client.get(f'/cart/add/{self.product.id}/?quantity=3')
        self.client.login(email="normal@crafts.com", password="password123")
        
        # Post checkout form with COD method and no screenshot
        post_data = {
            'payment_method': 'COD',
            'full_name': 'John Doe',
            'phone_number': '01222334455',
            'address': 'Alexandria, Egypt',
        }
        response = self.client.post('/checkout/', post_data)
        
        # Verify order created in DB
        order = Order.objects.filter(user=self.normal_user, payment_method='COD').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.full_name, 'John Doe')
        self.assertEqual(order.total_amount, Decimal('60.00')) # 20.00 * 3
        self.assertEqual(order.status, 'AWAITING_VERIFICATION')
        self.assertFalse(bool(order.payment_screenshot))
        
        # Verify order items
        order_item = OrderItem.objects.filter(order=order).first()
        self.assertIsNotNone(order_item)
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 3)
        
        # Verify cart was cleared
        session = self.client.session
        self.assertEqual(session.get('cart'), {})
        
        # Verify redirection to success page
        self.assertRedirects(response, f'/order/success/{order.id}/')

    def test_owner_orders_management(self):
        """
        Verify that owners can view and update order status, and non-owners are blocked.
        """
        from django.core.files.uploadedfile import SimpleUploadedFile
        from core.models import Order
        
        # Create an order
        mock_screenshot = SimpleUploadedFile(
            name='screenshot.png',
            content=b'receipt',
            content_type='image/png'
        )
        order = Order.objects.create(
            user=self.normal_user,
            full_name='Test Buyer',
            phone_number='01234567890',
            address='Giza, Egypt',
            total_amount=Decimal('20.00'),
            payment_screenshot=mock_screenshot,
            status='AWAITING_VERIFICATION'
        )
        
        # 1. Normal user cannot view order list or verify details
        self.client.login(email="normal@crafts.com", password="password123")
        response = self.client.get('/owners/orders/')
        self.assertRedirects(response, '/') # Access denied, goes to homepage
        
        # Cannot update status
        response = self.client.get(f'/owners/orders/{order.id}/status/CONFIRMED/')
        self.assertRedirects(response, '/')
        
        # 2. Owner user can access and verify
        self.client.logout()
        self.client.login(email="owner@crafts.com", password="password123")
        
        # Can see order list
        response = self.client.get('/owners/orders/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Buyer')
        
        # Can see detail page
        response = self.client.get(f'/owners/orders/{order.id}/')
        self.assertEqual(response.status_code, 200)
        
        # Can update status to CONFIRMED
        response = self.client.get(f'/owners/orders/{order.id}/status/CONFIRMED/', follow=True)
        order.refresh_from_db()
        self.assertEqual(order.status, 'CONFIRMED')

    def test_about_page_view(self):
        """
        Verify that the About Us page resolves, renders, and shows founder names.
        """
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/about.html')
        self.assertContains(response, "Soffian Elkadi")
        self.assertContains(response, "Yehia Fatouh")

    def test_soffian_owner_portal_button_visibility(self):
        """
        Verify that the Owner Portal button is shown in the navbar only for
        soffian.elkadi@littlecreators.shop.
        """
        # 1. Anonymous user - shouldn't see the warning button
        response = self.client.get('/')
        self.assertNotContains(response, "btn btn-warning")

        # 2. Other authenticated user - shouldn't see the warning button
        self.client.login(email="normal@crafts.com", password="password123")
        response = self.client.get('/')
        self.assertNotContains(response, "btn btn-warning")
        self.client.logout()

        # 3. Soffian user - should see the warning button
        soffian_user = CustomUser.objects.create_user(
            username="soffian",
            email="soffian.elkadi@littlecreators.shop",
            password="password123",
            is_owner=False,
            email_verified=True
        )
        self.client.login(email="soffian.elkadi@littlecreators.shop", password="password123")
        response = self.client.get('/')
        self.assertContains(response, "btn btn-warning")

    def test_amazon_style_category_search_filter(self):
        """
        Verify that the Amazon-style category select is present and works
        as part of the storefront search form.
        """
        # Get store catalog page
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Check that the select option is present
        self.assertContains(response, '<select name="category"')
        self.assertContains(response, '<option value="">All</option>')
        self.assertContains(response, f'<option value="{self.category.slug}">{self.category.name}</option>')
        
        # Test filtering using search and category parameters simultaneously
        response = self.client.get('/', {'category': self.category.slug, 'search': 'Spoon'})
        self.assertEqual(response.status_code, 200)
        # Wooden Spoon matches category and search
        self.assertContains(response, self.product.name)
        
        # Searching for 'Fork' in 'Woodwork' (draft product, or shouldn't match any published)
        response = self.client.get('/', {'category': self.category.slug, 'search': 'Fork'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.draft_product.name)
        # Wooden Spoon doesn't match 'Fork' query
        self.assertNotContains(response, self.product.name)

    def test_product_reviews_flow(self):
        """
        Verify that users can submit product reviews and rating average and review_count are updated.
        Verify manual overrides for owner work.
        """
        from core.models import Review
        # Login normal user
        self.client.login(email="normal@crafts.com", password="password123")
        
        # Submit review
        post_data = {
            'rating': '5',
            'comment': 'Awesome handcrafted woodwork, loved the quality!'
        }
        response = self.client.post(f'/product/{self.product.id}/review/', post_data)
        self.assertRedirects(response, f'/product/{self.product.slug}/')
        
        # Verify review created in DB
        review = Review.objects.filter(product=self.product, user=self.normal_user).first()
        self.assertIsNotNone(review)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Awesome handcrafted woodwork, loved the quality!')
        
        # Verify product rating and review count updated automatically
        self.product.refresh_from_db()
        self.assertEqual(self.product.review_count, 1)
        self.assertEqual(float(self.product.rating), 5.0)

        # Owner login and manual override check
        self.client.login(email="owner@crafts.com", password="password123")
        
        post_data = {
            'name': 'Wooden Spoon Updated',
            'category': self.category.id,
            'description': 'Updated description',
            'price': '25.00',
            'status': 'PUBLISHED',
            'rating': '4.8',
            'review_count': '150',
        }
        response = self.client.post(f'/owners/products/edit/{self.product.id}/', post_data)
        self.assertEqual(response.status_code, 302) # Redirect to product list
        
        # Verify changes in DB
        self.product.refresh_from_db()
        self.assertEqual(float(self.product.rating), 4.8)
        self.assertEqual(self.product.review_count, 150)


