# Crafts E-commerce Marketplace - Walkthrough

We have created the full-stack Django e-commerce platform **Crafts** using Bootstrap 5, SweetAlert2, and SQLite. The application compiles successfully, runs locally, and passes all automated unit tests.

---

## Technical Stack & Codebase Layout

- **Backend**: Python (Django), SQLite (fully prepared for PostgreSQL via Django ORM).
- **Frontend**: Bootstrap 5, Bootstrap Icons, SweetAlert2, Google Fonts (Outfit, Playfair Display).
- **Core App ([core](file:///d:/Dev/SoffianProject/core))**:
  - [models.py](file:///d:/Dev/SoffianProject/core/models.py): Defines schemas for `CustomUser` (extending `AbstractUser`), `Category` (preloaded with 5 artisan categories), `Product` (featuring active promotional price calculation logic), and `Promotion` (calculating percentage, fixed amounts, or special prices).
  - [translations.py](file:///d:/Dev/SoffianProject/core/translations.py) [NEW]: Contains Arabic key-value UI phrase mappings.
  - [templatetags/translate_tags.py](file:///d:/Dev/SoffianProject/core/templatetags/translate_tags.py) [NEW]: Simple-tag library providing `{% t "..." %}` lookups without GNU `gettext` requirements.
  - [views.py](file:///d:/Dev/SoffianProject/core/views.py): Store catalog layout, category filtering, search keyword querying, single product details rendering, and standard signup/login routes.
  - [urls.py](file:///d:/Dev/SoffianProject/core/urls.py): User portal routes.
  - **Templates**:
    - [base.html](file:///d:/Dev/SoffianProject/core/templates/core/base.html): Main layout file. It handles dynamic RTL stylesheet swaps, language selection forms, and SweetAlert2 notification flashes for Django messages.
    - [store.html](file:///d:/Dev/SoffianProject/core/templates/core/store.html): Grid layout with interactive translation blocks and "Add to Cart" SweetAlert triggers.
    - [product_detail.html](file:///d:/Dev/SoffianProject/core/templates/core/product_detail.html): Single item details page with image hover-zoom and detailed active promotion timing display.
    - [signup.html](file:///d:/Dev/SoffianProject/core/templates/core/signup.html) & [login.html](file:///d:/Dev/SoffianProject/core/templates/core/login.html): Glassmorphic panels with credentials helper boxes and OAuth simulation forms.
- **Owners App ([owners](file:///d:/Dev/SoffianProject/owners))**:
  - [views.py](file:///d:/Dev/SoffianProject/owners/views.py): Seller center analytics, product CRUD forms, category CRUD forms, promotion manager validators, and delete controllers.
  - [urls.py](file:///d:/Dev/SoffianProject/owners/urls.py): Owner portal paths, including `/owners/categories/...` routes.
  - **Templates**:
    - [base_owner.html](file:///d:/Dev/SoffianProject/owners/templates/owners/base_owner.html): Dedicated sidebar dashboard layout supporting RTL flipping.
    - [dashboard.html](file:///d:/Dev/SoffianProject/owners/templates/owners/dashboard.html): High-level metrics summaries.
    - [product_list.html](file:///d:/Dev/SoffianProject/owners/templates/owners/product_list.html): Inventory data grid.
    - [product_form.html](file:///d:/Dev/SoffianProject/owners/templates/owners/product_form.html): Real-time splitscreen preview form.
    - [category_list.html](file:///d:/Dev/SoffianProject/owners/templates/owners/category_list.html) [NEW]: Category list manager displaying icon previews.
    - [category_form.html](file:///d:/Dev/SoffianProject/owners/templates/owners/category_form.html) [NEW]: Add/edit category form featuring interactive Bootstrap icon badge selectors.
    - [promotion_list.html](file:///d:/Dev/SoffianProject/owners/templates/owners/promotion_list.html): Campaign dashboard listing current campaigns and active durations.
    - [promotion_form.html](file:///d:/Dev/SoffianProject/owners/templates/owners/promotion_form.html): Form hiding target fields depending on selected scope.
- **Static Files ([static](file:///d:/Dev/SoffianProject/static))**:
  - [style.css](file:///d:/Dev/SoffianProject/static/css/style.css): Custom stylesheet.
  - [preview.js](file:///d:/Dev/SoffianProject/static/js/preview.js): Event listeners for splitscreen live previews.

---

## Credentials for Testing

We preloaded the database with two active testing accounts:
- **Normal User (Customer)**:
  - **Email**: `user@crafts.com`
  - **Password**: `password123`
- **Store Owner (Seller)**:
  - **Email**: `owner@crafts.com`
  - **Password**: `password123`

---

## How to Run & Verify Locally

### 1. Launch the Server
Execute the run command to start Django's server:
```powershell
.venv\Scripts\python.exe manage.py runserver
```

### 2. Verify Translation / Language Toggle (`http://127.0.0.1:8000`)
- Navigate to the storefront.
- In the top-right navbar, change the language dropdown from **English** to **العربية**.
- Observe:
  - **RTL Flip**: The layout flips horizontally (logo on the right, menu links and search bar aligned correctly for Arabic).
  - **Translations**: UI labels, badges, buttons, descriptions, search bar placeholders, and cards flip dynamically to Arabic.
  - Change back to English to confirm layout flips back to LTR.

### 3. Verify Category CRUD in Owner Portal
- Log in as the owner: `owner@crafts.com` / `password123`.
- Navigate to `/owners` (or click **Owner Portal** in the storefront header).
- Click **Category Manager** (إدارة التصنيفات) in the left sidebar menu.
- **Add Category**:
  - Click **Add New Category** (إضافة تصنيف جديد).
  - Type name: `Embroidery` (التطريز).
  - Click on the suggested badge for `bi-palette` to auto-populate the icon input field, then click **Submit** (إرسال).
  - Verify that the category displays in the list with a rendered icon.
- **Storefront validation**:
  - Navigate to the storefront. Confirm that the new `Embroidery` category shows up in the sidebar filter.
- **Safety Deletion check**:
  - Try to delete `Ceramics & Pottery` category. Since it contains products, the system will block the action, displaying a SweetAlert warning warning you that it contains products.
  - Try to delete the newly created `Embroidery` category (which is empty). The SweetAlert warning pops up, click confirm, and verify it deletes successfully.

### 4. Verify Product CRUD & Splitscreen Live Preview
- Navigate to **Product Inventory** -> **Add New Product**.
- Observe the split screen: form on the left, empty card preview on the right.
- Fill out fields. As you type, the preview on the right renders the changes in real-time.
- Upload an image. The preview card loads the file locally using `FileReader` and displays it instantly.
- Toggle status between **Draft** and **Published** to see status badges change.
