from django.urls import path
from . import views

urlpatterns = [
    path('', views.store_view, name='store'),
    path('product/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),
    path('mock-oauth/<str:provider>/', views.mock_oauth_view, name='mock_oauth'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success_view, name='order_success'),
    path('about/', views.about_view, name='about'),
    path('product/<int:product_id>/review/', views.add_product_review, name='add_product_review'),
]
