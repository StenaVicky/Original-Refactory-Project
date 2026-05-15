"""
URL configuration for salesproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from saleapp import views 


urlpatterns = [
    path("/", views.home, name="home"),
    
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.create_category, name="create_category"),
    path("categories/<int:category_id>/delete/", views.delete_category, name="delete_category"),

    path("products/", views.product_list, name="product_list"),
    path("products/create/", views.create_product, name="create_product"),
    path("products/<int:product_id>/edit/", views.edit_product, name="edit_product"),
    path("products/<int:product_id>/delete/", views.delete_product, name="delete_product"),

    path("sales/create/", views.create_sale, name="create_sale"),
    path("sales/<int:sale_id>/invoice/", views.invoice, name="invoice"),
    path("sales/<int:sale_id>/edit/", views.edit_sale, name="edit_sale"),
    path("sales/<int:sale_id>/delete/", views.delete_sale, name="delete_sale"),
    path("sales/report/", views.sales_report, name="sales_report"),
    path("sales/report/export/", views.export_sales_report_excel, name="export_sales_report_excel"),
]