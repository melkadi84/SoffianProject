from django.urls import path
from . import views

urlpatterns = [
    path('', views.owner_dashboard, name='owner_dashboard'),
    path('products/', views.product_list, name='owner_product_list'),
    path('products/create/', views.product_create_or_edit, name='owner_product_create'),
    path('products/edit/<int:pk>/', views.product_create_or_edit, name='owner_product_edit'),
    path('products/delete/<int:pk>/', views.product_delete, name='owner_product_delete'),
    
    path('categories/', views.category_list, name='owner_category_list'),
    path('categories/create/', views.category_create_or_edit, name='owner_category_create'),
    path('categories/edit/<int:pk>/', views.category_create_or_edit, name='owner_category_edit'),
    path('categories/delete/<int:pk>/', views.category_delete, name='owner_category_delete'),
    
    path('promotions/', views.promotion_list, name='owner_promotion_list'),
    path('promotions/create/', views.promotion_create_or_edit, name='owner_promotion_create'),
    path('promotions/edit/<int:pk>/', views.promotion_create_or_edit, name='owner_promotion_edit'),
    path('promotions/delete/<int:pk>/', views.promotion_delete, name='owner_promotion_delete'),
    
    path('themes/', views.theme_list, name='owner_theme_list'),
    path('themes/activate/<int:pk>/', views.theme_activate, name='owner_theme_activate'),
    path('themes/change-font/', views.theme_change_font, name='owner_theme_change_font'),
    
    path('orders/', views.order_list, name='owner_order_list'),
    path('orders/bulk-delete/', views.order_bulk_delete, name='owner_order_bulk_delete'),
    path('orders/<int:pk>/', views.order_detail, name='owner_order_detail'),
    path('orders/<int:pk>/status/<str:status>/', views.order_update_status, name='owner_order_update_status'),
    path('configuration/', views.app_configuration_edit, name='owner_app_configuration'),
    path('categories/ajax-create/', views.ajax_category_create, name='owner_category_ajax_create'),
]
