from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from saleapp.models import Product, Sales
from .models import StockReceipt
from django.http import HttpResponse
from openpyxl import Workbook




def stock_receipt_list(request):
    receipts = StockReceipt.objects.all().order_by("-date_received")
    return render(request, "stock_receipt_list.html", {
        "receipts": receipts
    })


def create_stock_receipt(request):
    products = Product.objects.all()

    if request.method == "POST":
        product = get_object_or_404(Product, id=request.POST.get("product"))

        receipt = StockReceipt.objects.create(
            product=product,
            supplier_name=request.POST.get("supplier_name"),
            quantity_received=int(request.POST.get("quantity_received")),
            unit_cost=float(request.POST.get("unit_cost")),
            selling_price=float(request.POST.get("selling_price")),
            supplier_paid=request.POST.get("supplier_paid") == "on"
        )

        return redirect("goods_received_note", receipt_id=receipt.id)

    return render(request, "create_stock_receipt.html", {
        "products": products
    })


def goods_received_note(request, receipt_id):
    receipt = get_object_or_404(StockReceipt, id=receipt_id)

    return render(request, "goods_received_note.html", {
        "receipt": receipt
    })


def edit_stock_receipt(request, receipt_id):
    receipt = get_object_or_404(StockReceipt, id=receipt_id)
    products = Product.objects.all()

    if request.method == "POST":
        product = get_object_or_404(Product, id=request.POST.get("product"))

        receipt.product = product
        receipt.supplier_name = request.POST.get("supplier_name")
        receipt.quantity_received = int(request.POST.get("quantity_received"))
        receipt.unit_cost = float(request.POST.get("unit_cost"))
        receipt.supplier_paid = request.POST.get("supplier_paid") == "on"
        receipt.save()

        return redirect("goods_received_note", receipt_id=receipt.id)

    return render(request, "edit_stock_receipt.html", {
        "receipt": receipt,
        "products": products
    })


def delete_stock_receipt(request, receipt_id):
    receipt = get_object_or_404(StockReceipt, id=receipt_id)

    if request.method == "POST":
        receipt.delete()
        return redirect("stock_receipt_list")

    return render(request, "delete_stock_receipt.html", {
        "receipt": receipt
    })


def stock_report(request):
    products = Product.objects.all()
    report = []

    for product in products:
        total_received = StockReceipt.objects.filter(
            product=product
        ).aggregate(total=Sum("quantity_received"))["total"] or 0

        total_sold = Sales.objects.filter(
            product_name=product
        ).aggregate(total=Sum("quantity"))["total"] or 0

        current_stock = total_received - total_sold

        if current_stock <= 10:
            status = "Low Stock"
        elif current_stock <= 30:
            status = "Medium Stock"
        else:
            status = "High Stock"

        report.append({
            "product": product,
            "total_received": total_received,
            "total_sold": total_sold,
            "current_stock": current_stock,
            "status": status,
        })

    return render(request, "stock_report.html", {
        "report": report
    })

def export_stock_report_excel(request):
    products = Product.objects.all()

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Stock Report"

    worksheet.append([
        "Product",
        "Category",
        "Total Received",
        "Total Sold",
        "Current Stock",
        "Status"
    ])

    for product in products:
        total_received = StockReceipt.objects.filter(
            product=product
        ).aggregate(total=Sum("quantity_received"))["total"] or 0

        total_sold = Sales.objects.filter(
            product=product
        ).aggregate(total=Sum("quantity"))["total"] or 0

        current_stock = total_received - total_sold

        if current_stock <= 5:
            status = "Low Stock"
        elif current_stock <= 20:
            status = "Medium Stock"
        else:
            status = "High Stock"

        worksheet.append([
            product.product_name,
            product.category,
            total_received,
            total_sold,
            current_stock,
            status
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = 'attachment; filename="stock_report.xlsx"'

    workbook.save(response)

    return response