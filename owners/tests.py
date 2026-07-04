from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from core.models import CustomUser, Category, Product
from decimal import Decimal
import io
import uuid
import zipfile

class OwnerCSVTests(TestCase):
    def setUp(self):
        # Generate random unique credentials to avoid hardcoding
        self.owner_username = "owner_" + uuid.uuid4().hex[:10]
        self.owner_email = f"{self.owner_username}@test.com"
        self.owner_password = "Pass_" + uuid.uuid4().hex[:10]

        self.owner_user = CustomUser.objects.create_user(
            username=self.owner_username,
            email=self.owner_email,
            password=self.owner_password,
            is_owner=True,
            email_verified=True
        )

        self.normal_username = "normal_" + uuid.uuid4().hex[:10]
        self.normal_email = f"{self.normal_username}@test.com"
        self.normal_password = "Pass_" + uuid.uuid4().hex[:10]

        self.normal_user = CustomUser.objects.create_user(
            username=self.normal_username,
            email=self.normal_email,
            password=self.normal_password,
            is_owner=False,
            email_verified=True
        )
        self.client = Client()

    def test_export_template_as_owner(self):
        self.client.login(email=self.owner_email, password=self.owner_password)
        response = self.client.get(reverse('owner_product_export_template'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Verify content
        content = response.content.decode('utf-8')
        lines = content.strip().split('\r\n')
        self.assertGreater(len(lines), 1)
        headers = lines[0].split(',')
        self.assertEqual(headers, ['name', 'category', 'description', 'price', 'status', 'rating', 'review_count', 'image_url'])

    def test_export_template_unauthorized(self):
        # Normal user login
        self.client.login(email=self.normal_email, password=self.normal_password)
        response = self.client.get(reverse('owner_product_export_template'))
        self.assertEqual(response.status_code, 302) # Redirect to store or access denied

        # No login
        self.client.logout()
        response = self.client.get(reverse('owner_product_export_template'))
        self.assertEqual(response.status_code, 302) # Redirect to login

    def test_import_csv_success(self):
        self.client.login(email=self.owner_email, password=self.owner_password)
        csv_content = (
            "name,category,description,price,status,rating,review_count,image_url\n"
            "Handmade Plate,Pottery,A classic hand-painted clay plate.,150.00,PUBLISHED,4.9,20,\n"
            "Woven Basket,Baskets,Beautiful palm leaf woven storage basket.,80.00,DRAFT,4.2,5,\n"
        )
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'test_products.csv'
        
        response = self.client.post(reverse('owner_product_import_csv'), {'csv_file': csv_file})
        self.assertEqual(response.status_code, 302)
        
        # Verify redirect to list
        self.assertRedirects(response, reverse('owner_product_list'))

        # Verify products were imported
        self.assertEqual(Product.objects.count(), 2)
        plate = Product.objects.get(name="Handmade Plate")
        self.assertEqual(plate.category.name, "Pottery")
        self.assertEqual(plate.price, Decimal("150.00"))
        self.assertEqual(plate.status, "PUBLISHED")
        self.assertEqual(plate.rating, Decimal("4.9"))
        self.assertEqual(plate.review_count, 20)

        basket = Product.objects.get(name="Woven Basket")
        self.assertEqual(basket.category.name, "Baskets")
        self.assertEqual(basket.price, Decimal("80.00"))
        self.assertEqual(basket.status, "DRAFT")
        self.assertEqual(basket.rating, Decimal("4.2"))
        self.assertEqual(basket.review_count, 5)

    def test_import_csv_validation_failure_rolls_back(self):
        self.client.login(email=self.owner_email, password=self.owner_password)
        # Row 3 has invalid price, Row 4 has empty category
        csv_content = (
            "name,category,description,price,status,rating,review_count,image_url\n"
            "Good Item,Pottery,Valid item,50.00,PUBLISHED,4.0,5,\n"
            "Bad Item 1,Pottery,Invalid price,-10.00,PUBLISHED,4.0,5,\n"
            "Bad Item 2,,No category,30.00,PUBLISHED,4.0,5,\n"
        )
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'test_products.csv'
        
        response = self.client.post(reverse('owner_product_import_csv'), {'csv_file': csv_file})
        self.assertEqual(response.status_code, 302)
        
        # Verify that absolutely NO products were created due to rollback
        self.assertEqual(Product.objects.count(), 0)
        
        # Verify errors are in session
        self.assertIn('import_errors', self.client.session)
        errors = self.client.session['import_errors']
        self.assertEqual(len(errors), 2)
        self.assertIn("Row 3: Price must be greater than zero.", errors[0])
        self.assertIn("Row 4: Category name is required.", errors[1])

    def test_database_backup_export(self):
        self.client.login(email=self.owner_email, password=self.owner_password)
        cat = Category.objects.create(name="Wood", icon="bi-tree")
        Product.objects.create(name="Bowl", category=cat, description="Bowl desc", price=Decimal("10.00"), status="PUBLISHED")
        
        response = self.client.post(reverse('owner_database_backup_restore'), {'action': 'export'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertIn('attachment', response['Content-Disposition'])
        
        zip_data = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_data) as zip_file:
            files = zip_file.namelist()
            self.assertIn('users.csv', files)
            self.assertIn('categories.csv', files)
            self.assertIn('products.csv', files)

    def test_database_reset_unauthorized(self):
        self.client.login(email=self.normal_email, password=self.normal_password)
        response = self.client.get(reverse('owner_database_reset'))
        self.assertEqual(response.status_code, 302)

    def test_database_reset_success(self):
        self.client.login(email=self.owner_email, password=self.owner_password)
        cat = Category.objects.create(name="ResetCat")
        Product.objects.create(name="ResetProd", category=cat, description="Reset description", price=Decimal("20.00"))
        
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Category.objects.count(), 1)

        response = self.client.post(reverse('owner_database_reset'), {'confirmation_phrase': 'WRONG'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.count(), 1)

        response = self.client.post(reverse('owner_database_reset'), {'confirmation_phrase': 'RESET DATABASE'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Category.objects.count(), 0)
        self.assertTrue(CustomUser.objects.filter(email=self.owner_email).exists())
