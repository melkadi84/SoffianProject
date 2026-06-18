# Crafts Instapay Checkout & Orders Management Implementation Plan

We are adding a complete **Instapay Checkout & Order Verification** system:
1. **Shopping Cart & Checkout Flow**: Customers can add items to a session-based cart, adjust quantities, proceed to a checkout page displaying Instapay transfer instructions (Instapay ID, Phone, QR Code placeholder), fill in shipping details, and upload a payment transfer receipt screenshot.
2. **Owner Orders Manager**: Store owners can access a new "Orders Manager" dashboard where they see all orders, view uploaded Instapay screenshot receipts, and click **Confirm Payment** (to approve and process) or **Reject Payment** (to cancel).

---

## User Review Required

> [!IMPORTANT]
> **Session-based Cart**: To ensure quick performance and database efficiency, we will store the shopping cart items in the user's session (`request.session['cart']`). This avoids writing temporary records to SQLite and enables guest or unauthenticated browsing of cart items before checking out.
>
> **Instapay screenshot uploads**: Instapay receipt screenshots will be uploaded to the `media/screenshots/` folder. The owner dashboard will display these screenshots with a modal overlay so the owner can verify the transfer details and match the amount before confirming the order.

---

## Proposed Changes

### 1. Database Model Additions

#### [MODIFY] [core/models.py](file:///d:/Dev/SoffianProject/core/models.py)
Add the following models:
- **`Order`**:
  - `user`: ForeignKey to CustomUser.
  - `full_name` (CharField)
  - `address` (TextField)
  - `phone_number` (CharField)
  - `total_amount` (DecimalField)
  - `payment_screenshot` (ImageField, upload_to='screenshots/')
  - `status` (choices: 'AWAITING_VERIFICATION', 'CONFIRMED', 'SHIPPED', 'CANCELLED', default='AWAITING_VERIFICATION')
  - `created_at` (DateTimeField, auto_now_add=True)
- **`OrderItem`**:
  - `order`: ForeignKey to Order (related_name='items').
  - `product`: ForeignKey to Product.
  - `quantity` (IntegerField)
  - `price` (DecimalField) - price at time of purchase.

### 2. URL Router Additions

#### [MODIFY] [core/urls.py](file:///d:/Dev/SoffianProject/core/urls.py)
Add cart and checkout endpoints:
- `/cart/` (view cart)
- `/cart/add/<id>/` (add item to cart)
- `/cart/remove/<id>/` (remove item from cart)
- `/checkout/` (shipping + Instapay receipt screenshot upload)
- `/order/success/<id>/` (confirmation receipt screen)

#### [MODIFY] [owners/urls.py](file:///d:/Dev/SoffianProject/owners/urls.py)
Add order management endpoints:
- `/owners/orders/` (list all orders)
- `/owners/orders/<id>/` (view order details & verify screenshot)
- `/owners/orders/<id>/status/<status>/` (approve/reject/ship order status update)

### 3. Controller Logic Implementations

#### [MODIFY] [core/views.py](file:///d:/Dev/SoffianProject/core/views.py)
- Implement `cart_add` & `cart_remove` to manipulate `request.session['cart']`.
- Implement `cart_view` to render cart items and totals.
- Implement `checkout_view`:
  - Enforces login (to track orders).
  - Displays the Instapay payment info panel and file upload input.
  - On submit: creates `Order` and `OrderItem` records, saves the uploaded screenshot, clears the session cart, and redirects to success page.
- Implement `order_success_view` showing purchase summaries.

#### [MODIFY] [owners/views.py](file:///d:/Dev/SoffianProject/owners/views.py)
- Update `owner_dashboard` analytics context to show "Pending Orders" count.
- Implement `order_list` showing all orders with statuses.
- Implement `order_detail` displaying shipping parameters, items bought, and the uploaded receipt screenshot.
- Implement `order_update_status` allowing status changes (Confirm Payment, Ship, Cancel).

### 4. Layout & UI Localizations

- **Navigation Bars**:
  - Update `base.html` to add a cart icon link showing the number of items in the cart dynamically using a small context processor or session read.
  - Update `base_owner.html` to add an **Orders Manager** link in the sidebar menu.

#### [NEW] [cart.html](file:///d:/Dev/SoffianProject/core/templates/core/cart.html)
- Interactive cart screen displaying selected items, subtotal, and checkout triggers.

#### [NEW] [checkout.html](file:///d:/Dev/SoffianProject/core/templates/core/checkout.html)
- Shipping details form alongside an **Instapay payment panel** explaining the transfer instructions (Instapay ID: `crafts@instapay`, Phone: `01234567890`), showing a mock QR code, and providing a file upload input.

#### [NEW] [order_success.html](file:///d:/Dev/SoffianProject/core/templates/core/order_success.html)
- Success page confirming the order has been submitted for verification, displaying the order ID and summary.

#### [NEW] [order_list.html](file:///d:/Dev/SoffianProject/owners/templates/owners/order_list.html) & [order_detail.html](file:///d:/Dev/SoffianProject/owners/templates/owners/order_detail.html)
- Listing pages for orders and detailed lookup screens showing order parameters and screenshot verification panels.

---

## Verification Plan

### Automated Tests
- Implement tests in `core/tests.py` testing:
  - Adding and removing items from the session cart.
  - Creating an order reduces or processes items and saves the payment screenshot.
  - Non-owners cannot access the order manager panel.

### Manual Verification
- Add items to the cart from the storefront. Go to `/cart/`.
- Proceed to `/checkout/`, enter shipping parameters.
- Review Instapay instructions. Upload a sample screenshot image. Click place order.
- Verify redirect to `/order/success/` and that the session cart is cleared.
- Login as owner. Go to `/owners/orders/`. Find the order (status: Awaiting Verification).
- View order details. Expand the Instapay screenshot. Click **Confirm Payment**.
- Verify order status updates to Confirmed and storefront details update.
