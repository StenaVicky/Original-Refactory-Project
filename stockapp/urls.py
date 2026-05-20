from django.urls import path
from stockapp import views



urlpatterns = [
    path("receipts/", views.stock_receipt_list, name="stock_receipt_list"),
    path("receipts/create/", views.create_stock_receipt, name="create_stock_receipt"),
    path("receipts/<int:receipt_id>/grn/", views.goods_received_note, name="goods_received_note"),
    path("receipts/<int:receipt_id>/edit/", views.edit_stock_receipt, name="edit_stock_receipt"),
    path("receipts/<int:receipt_id>/delete/", views.delete_stock_receipt, name="delete_stock_receipt"),
    path("report/", views.stock_report, name="stock_report"),
    path("report/export/", views.export_stock_report_excel, name="export_stock_report_excel"),
    path("supplier_report/", views.supplier_report, name="supplier_report"),  
]