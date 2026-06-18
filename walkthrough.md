# Crafts E-commerce Marketplace - Walkthrough

We have created the full-stack Django e-commerce platform **Crafts** using Bootstrap 5, SweetAlert2, and SQLite. The application compiles successfully, runs locally, and passes all automated unit tests.

---

## Technical Stack & Codebase Layout

- **Backend**: Python (Django), SQLite (fully prepared for PostgreSQL via Django ORM).
- **Frontend**: Bootstrap 5, Bootstrap Icons, SweetAlert2, Google Fonts (Outfit, Playfair Display).
- **Core App ([core](file:///d:/Dev/SoffianProject/core))**:
  - [models.py](file:///d:/Dev/SoffianProject/core/models.py): Defines schemas for `CustomUser` (extending `AbstractUser`), `Category` (preloaded with 5 artisan categories), `Product` (featuring active promotional price calculation logic), and `Promotion` (calculating percentage, fixed amounts, or special prices).
  - [views.py](file:///d:/Dev/SoffianProject/core/views.py): Store catalog layout, category filtering, search keyword querying, single product details rendering, and standard signup/login routes.
  - [urls.py](file:///d:/Dev/SoffianProject/core/urls.py): User portal routes.
  - **Templates**:
    - [base.html](file:///d:/Dev/SoffianProject/core/templates/core/base.html): Main layout file. It imports assets and handles SweetAlert2 notification flashes for Django messages.
    - [store.html](file:///d:/Dev/SoffianProject/core/templates/core/store.html): Grid layout with interactive "Add to Cart" SweetAlert triggers.
    - [product_detail.html](file:///d:/Dev/SoffianProject/core/templates/core/product_detail.html): Single item details page with image hover-zoom and detailed active promotion timing display.
    - [signup.html](file:///d:/Dev/SoffianProject/core/templates/core/signup.html) & [login.html](file:///d:/Dev/SoffianProject/core/templates/core/login.html): Glassmorphic panels with credentials helper boxes and OAuth simulation forms.
- **Owners App ([owners](file:///d:/Dev/SoffianProject/owners))**:
  - [views.py](file:///d:/Dev/SoffianProject/owners/views.py): Seller center analytics, product CRUD forms, promotion manager validators, and delete controllers.
  - [urls.py](file:///d:/Dev/SoffianProject/owners/urls.py): Owner portal paths.
  - **Templates**:
    - [base_owner.html](file:///d:/Dev/SoffianProject/owners/templates/owners/base_owner.html): Dedicated sidebar dashboard layout.
    - [dashboard.html](file:///d:/Dev/SoffianProject/owners/templates/owners/dashboard.html): High-level metrics summaries.
    - [product_list.html](file:///d:/Dev/SoffianProject/owners/templates/owners/product_list.html): Inventory data grid.
    - [product_form.html](file:///d:/Dev/SoffianProject/owners/templates/owners/product_form.html): Real-time splitscreen preview form.
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

### 2. Verify Normal User Portal (`https://127.0.0.1:8000`)
- **Browsing & Filters**:
  - Navigate to the homepage.
  - Click different category filters in the left sidebar (e.g. *Ceramics*, *Woodworking*). Verify products change accordingly.
  - Search for "Mahogany" or "Mug" using the search box to check search queries.
- **Product Details & Discounts**:
  - Click on "View Details" on the **Handmade Rustic Ceramic Mug**.
  - Notice it is marked on sale. The price is struck out and shows a red sale price. It also displays a warning banner showing the active promotion title and when it expires.
  - Hover over the image to trigger the hover zoom effect.
  - Click "Add to Cart" to see the SweetAlert confirmation toast.
- **Authentication Flows**:
  - Log out and click **Sign Up**.
  - Fill out the form. Once submitted, check the terminal logs where the Django development server is running. You will see a simulated verification email containing a link like `http://127.0.0.1:8000/verify-email/<token>/`.
  - Copy and paste that link in your browser to activate your account and log in.
  - Test mock third-party sign-ins by clicking the **Google** or **Apple** login buttons to instantly sign in with pre-verified profiles.

### 3. Verify Owner Portal (`https://127.0.0.1:8000/owners`)
- **Owner Dashboard**:
  - Sign in with `owner@crafts.com` / `password123` and click **Owner Portal** in the navigation bar.
  - Check the analytics cards (Total Products, Active Promotions, Draft Products, Categories) and quick listing summaries.
- **Product CRUD & Real-Time Live Preview**:
  - Click **Product Inventory** -> **Add New Product**.
  - On the left side, fill out the form. As you type the name or price, note that the preview card on the right updates instantly in real-time.
  - Upload a local image file. Observe that the preview image updates instantly.
  - Set the status to **Draft** and click **Publish Product**.
  - Go to the storefront. Confirm that the draft item is *not* visible to normal users.
  - Edit the product, change its status to **Published**, and verify it is now displayed on the main storefront.
  - Delete a product and verify the SweetAlert warning modal intercepts the action before execution.
- **Promotion Scheduler**:
  - Go to **Promotions Scheduler** -> **New Promotion**.
  - In **Promotion Target Scope**, select **Per Category**. Note that the *Target Category* dropdown displays while the *Target Product* dropdown remains hidden.
  - Select Woodworking, set discount type to Percentage, value to 25%, and specify start and end dates.
  - Click **Schedule Campaign**.
  - Go back to the storefront. Verify that all items under Woodworking now reflect the 25% discount and display sale badges.

---

## Updates (June 2026)

### 1. About Us Page
- Added a gorgeous, responsive **About Us** page (`/about/`) accessible from both the header navigation bar and the footer.
- Showcases the project origin narrative and profiles of the two co-founders:
  - **Soffian Elkadi** (Co-Founder & Lead Designer): Styled profile card with portrait image (`soffian.png`) and bio description.
  - **Yehia Fatouh** (Co-Founder & Operations Head): Styled profile card with portrait image (`yehia.png`) and bio description.
- Portrait images are saved in `static/images/owners/`.

### 2. Instapay Payment & QR Code Update
- Updated the checkout page (`checkout.html`) with the real Instapay ID: `soffian.elkadi@instapay`.
- Added a clickable payment link pointing to `https://ipn.eg/S/soffian.elkadi/instapay/8KvIio`.
- Replaced the mock SVG QR code with the real uploaded QR code image (`instapay_qr.png`) stored in `static/images/`.
- Wrapped Instapay instructions, helper messages, and inputs with `{% t %}` tags for full translation.

### 3. Typography & Contrast Fixes
- Fixed the global font-family styling: dynamic Arabic and English fonts configured in the Theme Manager are now correctly applied to headings (`h1` through `h6`), inputs, buttons, and textareas across all portals (Main & Owner).
- Fixed text contrast in the dark footer (`footer-crafts`): changed Bootstrap's `.text-muted` and normal text styles to a warmer, higher-contrast beige color scheme (`#bfaea5` and `#d9cfc7`) to make all links and credential helpers fully legible.

