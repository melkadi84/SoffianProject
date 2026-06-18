# Crafts E-commerce Platform Implementation Plan

We are building a full-stack Django e-commerce platform called **Crafts**. The application will feature a modern, responsive user interface utilizing Bootstrap 5, SweetAlert2, and standard Django templates. It will contain two distinct portals:
1. **User Portal (`/`)**: Main customer-facing storefront featuring category filters, search, product detail views, custom user authentication (with mock flows for Google/Apple/Mobile and fully functional Email signup/verification), and custom carousels.
2. **Owner Portal (`/owners`)**: Admin/seller dashboard containing product management (CRUD), real-time live preview for adding/editing products, draft/published status, and a versatile promotions manager (applying discounts or special prices to single items, whole categories, or all items over a specific duration).

---

## User Review Required

> [!IMPORTANT]
> **Authentication Mocking**: To simulate Google, Apple, and Mobile sign-up/sign-in flows realistically without requiring external API keys, we will implement high-fidelity simulated OAuth login routes. Email signup will support verification (with verification tokens and link logging to the console during development). Please let us know if you prefer integrating a specific package like `django-allauth` for production-grade third-party OAuth, or if high-fidelity simulation is sufficient for this stage.
> 
> **Database**: We will use SQLite for local development, utilizing Django's database backend abstraction to make it fully ready to migrate to PostgreSQL. We will ensure all custom database queries use Django's ORM so that no raw SQLite dialect is written, enabling zero-config migration to PostgreSQL.

---

## Proposed Changes

We will create a standard Django project layout:
- Virtual environment in `d:\Dev\SoffianProject\.venv`
- Project folder: `d:\Dev\SoffianProject` with Django project `crafts_project` and two apps: `core` (shared models and user portal) and `owners` (owner/admin portal).

### 1. Environment Setup

- Create a virtual environment `.venv` and install:
  - `django`
  - `pillow` (for handling product images)

### 2. Core Models (`core/models.py`)

- **`CustomUser`**: Extends `AbstractUser`. Includes fields:
  - `phone_number` (optional, for mobile signup)
  - `email_verified` (boolean, default False)
  - `auth_provider` (choices: 'EMAIL', 'GOOGLE', 'APPLE', 'MOBILE')
  - `is_owner` (boolean, default False, to easily test owner dashboard access)
- **`Category`**:
  - `name` (string)
  - `slug` (slug, unique)
  - `icon` (string, Bootstrap Icons class name or emoji)
- **`Product`**:
  - `name` (string)
  - `slug` (slug)
  - `category` (ForeignKey to Category)
  - `description` (text)
  - `price` (decimal)
  - `image` (ImageField, fallback to placeholder if not uploaded)
  - `status` (choices: 'DRAFT', 'PUBLISHED', default 'DRAFT')
  - `created_at` (datetime)
  - `updated_at` (datetime)
- **`Promotion`**:
  - `name` (string)
  - `discount_type` (choices: 'PERCENTAGE', 'FIXED_AMOUNT', 'SPECIAL_PRICE')
  - `discount_value` (decimal)
  - `scope` (choices: 'ALL', 'CATEGORY', 'PRODUCT')
  - `category` (ForeignKey to Category, optional)
  - `product` (ForeignKey to Product, optional)
  - `start_date` (datetime)
  - `end_date` (datetime)
  - `is_active` (boolean, default True)

We will implement custom properties on the `Product` model to calculate active promotions. The logic will automatically search for the highest active discount applicable to a product by checking:
1. Direct product-specific promotions.
2. Category promotions.
3. Global promotions (all items).

### 3. Core App (User Storefront)

- **Templates (`core/templates/core/`)**:
  - `base.html`: Main layout using Bootstrap 5, SweetAlert2, and Google Fonts (Outfit or Inter). Styled with custom dark mode & luxury warm accents.
  - `store.html`: Amazon-like landing page containing:
    - Featured slider/carousel for current sales and top categories.
    - Category filter sidebar/pills.
    - Product grid with cards showing regular price, discounted price (if active), sale badges, and Add-to-Cart buttons.
    - Search input.
  - `product_detail.html`: Multi-column details page with:
    - Large product image with hover zoom.
    - Product title, description, category, and review stars (mocked).
    - Clear display of active discount details (e.g. "Save $20 until June 20!").
    - Quantity selector and CTA buttons.
  - `signup.html` & `login.html`: Custom forms supporting standard email signups and featuring beautiful Google, Apple, and Mobile simulated sign-in options.
  - `verify_email.html`: Landing page for clicking the email verification link.
- **Views (`core/views.py`)**:
  - `store_view`: Handles search, category filtering, and product queries.
  - `product_detail_view`: Detailed single-product view (draft products can only be accessed by authenticated owners).
  - `signup_view`, `login_view`, `logout_view`: Standard Django auth + mock auth triggers.
  - `verify_email_view`: Activates the user profile upon receiving a valid token.
  - `mock_oauth_callback`: Standardized endpoint to simulate external signups.

### 4. Owners App (Dashboard & Management)

- **Templates (`owners/templates/owners/`)**:
  - `dashboard.html`: Analytics dashboard showing products, promotions, draft counts, and general inventory overview.
  - `product_form.html`: The add/edit product interface featuring a **split-screen live preview panel**. Using Vanilla JavaScript, as the owner types the product name, adjusts the price, writes the description, or selects an image file, the preview card instantly updates to show exactly how it will look on the storefront.
  - `product_list.html`: Product list table with search/filters and edit/delete triggers using SweetAlert2 confirmation dialogs.
  - `promotion_form.html`: Promotion scheduler form allowing target selection (all items, category, or single item), type (percentage, fixed amount, special price), discount value, and date range.
  - `promotion_list.html`: Shows all promotions, highlighting currently active vs. scheduled vs. expired promotions.
- **Views (`owners/views.py`)**:
  - `owner_dashboard`: Owner-only landing page.
  - `product_create_or_edit`: Form handler for CRUD.
  - `product_delete`: Deletes a product (handles cleanup of its image).
  - `promotion_create_or_edit`: Form handler for creating/modifying sales.
  - `promotion_delete`: Deletes an offer.

### 5. Styling and Custom JS (`static/`)

- `static/css/style.css`: Modern warm aesthetic with glassmorphism cards, deep dark headers, subtle micro-animations (scale effects on cards, hover glowing buttons, custom badges).
- `static/js/preview.js`: Event listeners on fields in the product form to dynamically write to the preview template (utilizes `FileReader` for image file inputs).
- `static/js/alerts.js`: SweetAlert2 helper functions for standard messages (success toasts, deletion confirmation modals).

---

## Verification Plan

### Automated Verification
- Write Django tests in `core/tests.py` verifying:
  - Product model promotion precedence rules (Product-specific vs. Category-specific vs. Global).
  - Normal users cannot access draft products.
  - Authentication permission checks (only owners/staff can access `/owners/` paths).

### Manual Verification
- **User Flow**:
  - Open customer storefront, verify products display with and without active promotional discounts.
  - Test filtering by category and search.
  - Test standard Email signup, verify token link prints in the terminal, click link to verify.
  - Test mock Google/Apple/Mobile authentication.
- **Owner Flow**:
  - Navigate to `/owners`.
  - Add a product, verify the live preview matches the input in real-time, including uploading a temporary image.
  - Save as draft, verify it does not appear in customer storefront.
  - Edit product, change to published, verify it appears in the storefront.
  - Add a promotion for a product's category, verify the product card shows the discounted price and discount badge in the storefront.
  - Delete product/promotion and verify SweetAlert2 dialog works.
