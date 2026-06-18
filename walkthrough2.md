# Crafts E-commerce Marketplace - Walkthrough

We have created the full-stack Django e-commerce platform **Crafts** using Bootstrap 5, SweetAlert2, and SQLite. The application compiles successfully, runs locally, and passes all automated unit tests.

---

## Technical Stack & Codebase Layout

- **Backend**: Python (Django), SQLite (fully prepared for PostgreSQL via Django ORM).
- **Frontend**: Bootstrap 5, Bootstrap Icons, SweetAlert2, Google Fonts (Outfit, Playfair Display).
- **Core App ([core](file:///d:/Dev/SoffianProject/core))**:
  - [models.py](file:///d:/Dev/SoffianProject/core/models.py): Defines schemas for `CustomUser` (AbstractUser), `Category` (5 default categories), `Product` (calculated promotional rates), `Promotion` (scopes for single items, categories, or global), and `Theme` [NEW] (colors configuration database).
  - [translations.py](file:///d:/Dev/SoffianProject/core/translations.py): Contains Arabic key-value UI phrase mappings.
  - [templatetags/translate_tags.py](file:///d:/Dev/SoffianProject/core/templatetags/translate_tags.py): Simple-tag library providing `{% t "..." %}` lookups without GNU `gettext` requirements.
  - [context_processors.py](file:///d:/Dev/SoffianProject/core/context_processors.py) [NEW]: Injects the active theme dynamically into all template render threads.
  - [views.py](file:///d:/Dev/SoffianProject/core/views.py): Store catalog, category filter, detail views, and standard signup/login views.
  - [urls.py](file:///d:/Dev/SoffianProject/core/urls.py): User portal routes.
- **Owners App ([owners](file:///d:/Dev/SoffianProject/owners))**:
  - [views.py](file:///d:/Dev/SoffianProject/owners/views.py): Seller center analytics, product CRUD forms, category CRUD forms, theme manager views [NEW], and delete controller handles.
  - [urls.py](file:///d:/Dev/SoffianProject/owners/urls.py): Owner portal paths, including Category CRUD and Themes Manager routes.
  - **Templates**:
    - [base.html](file:///d:/Dev/SoffianProject/core/templates/core/base.html) & [base_owner.html](file:///d:/Dev/SoffianProject/owners/templates/owners/base_owner.html): Layout shells. Supports RTL layout flipping, locale selectors, and dynamic inline CSS variables overrides based on the active database `theme`.
    - [dashboard.html](file:///d:/Dev/SoffianProject/owners/templates/owners/dashboard.html): High-level metrics summaries.
    - [product_list.html](file:///d:/Dev/SoffianProject/owners/templates/owners/product_list.html): Inventory data grid.
    - [product_form.html](file:///d:/Dev/SoffianProject/owners/templates/owners/product_form.html): Real-time splitscreen preview form.
    - [category_list.html](file:///d:/Dev/SoffianProject/owners/templates/owners/category_list.html) & [category_form.html](file:///d:/Dev/SoffianProject/owners/templates/owners/category_form.html): Category manager dashboard and forms.
    - [theme_list.html](file:///d:/Dev/SoffianProject/owners/templates/owners/theme_list.html) [NEW]: Visual Themes Manager card dashboard.
    - [promotion_list.html](file:///d:/Dev/SoffianProject/owners/templates/owners/promotion_list.html) & [promotion_form.html](file:///d:/Dev/SoffianProject/owners/templates/owners/promotion_form.html): Promotions tables and schedules.
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

### 2. Verify Themes Manager (Portal Colors Customization)
- Log in as the owner: `owner@crafts.com` / `password123`.
- Navigate to `/owners` (or click **Owner Portal** in the storefront header).
- Click **Themes Manager** (مدير المظاهر) in the left sidebar menu.
- **10 Global Portal Themes**:
  - You will see 10 preloaded themes inspired by famous portals:
    1. **Crafts Classic**: Default warm artisan leather theme.
    2. **Amazon Amber**: Yellow primary color and charcoal headers.
    3. **Etsy Tangerine**: Orange accents and cream backgrounds.
    4. **Shopify Premium**: Mint green branding.
    5. **eBay Bright**: Signature corporate blue color schemes.
    6. **IKEA Bright Blue**: Classic blue and yellow highlight accents.
    7. **Apple Minimalist**: Sleek monochrome gray/black buttons.
    8. **Netflix Dark Crimson**: Full dark mode background (#141414) with crimson red highlights.
    9. **GitHub Slate**: Code slate-grey headers and repository-blue links.
    10. **Target Energetic Red**: Cherry red badges and grey borders.
- **Activation**:
  - Hover over the colored circular swatches representing each theme's hex values.
  - Click **Activate** (تنشيط) on the **Netflix Dark Crimson** theme.
  - Verify that the entire layout immediately toggles to Netflix's sleek dark mode with crimson highlights.
  - Open the customer storefront in another tab ([http://127.0.0.1:8000](http://127.0.0.1:8000)) and confirm that the storefront colors have updated instantly to Netflix's layout.
  - Navigate back to Themes Manager and activate **Shopify Premium** or **Amazon Amber** and confirm colors change instantly.

### 3. Verify Translation / Language Toggle (`http://127.0.0.1:8000`)
- Navigate to the storefront.
- In the top-right navbar, change the language dropdown from **English** to **العربية**.
- Observe:
  - **RTL Flip**: The layout flips horizontally (logo on the right, menu links and search bar aligned correctly for Arabic).
  - **Translations**: UI labels, badges, buttons, descriptions, search bar placeholders, and cards flip dynamically to Arabic.
  - Change back to English to confirm layout flips back to LTR.

### 4. Verify Category CRUD in Owner Portal
- Log in as the owner: `owner@crafts.com` / `password123`.
- Navigate to `/owners` -> **Category Manager** (إدارة التصنيفات) in the left sidebar menu.
- **Add Category**:
  - Click **Add New Category** (إضافة تصنيف جديد).
  - Type name: `Embroidery` (التطريز).
  - Click on the suggested badge for `bi-palette` to auto-populate the icon input field, then click **Submit** (إرسال).
  - Verify that the category displays in the list with a rendered icon.
- **Safety Deletion check**:
  - Try to delete `Ceramics & Pottery` category. Since it contains products, the system will block the action, displaying a SweetAlert warning warning you that it contains products.
  - Try to delete the newly created `Embroidery` category (which is empty). The SweetAlert warning pops up, click confirm, and verify it deletes successfully.

### 5. Verify Product CRUD & Splitscreen Live Preview
- Navigate to **Product Inventory** -> **Add New Product**.
- Observe the split screen: form on the left, empty card preview on the right.
- Fill out fields. As you type, the preview on the right renders the changes in real-time.
- Upload an image. The preview card loads the file locally using `FileReader` and displays it instantly.
- Toggle status between **Draft** and **Published** to see status badges change.
