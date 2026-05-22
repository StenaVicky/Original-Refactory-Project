from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from saleapp.models import Product, SaleItem
from .models import StockReceipt
from django.http import HttpResponse
from openpyxl import Workbook
from decimal import Decimal




def stock_receipt_list(request):
    receipts = StockReceipt.objects.all().order_by("-date_received")
    return render(request, "stock_receipt_list.html", {
        "receipts": receipts
    })


def create_stock_receipt(request):
    products = Product.objects.all()

    if request.method == "POST":
        product = get_object_or_404(Product, id=request.POST.get("product"))
        supplier_name = request.POST.get("supplier_name")
        try:
            quantity_received = int(request.POST.get("quantity_received", 0))
            unit_cost = Decimal(request.POST.get("unit_cost"))
            selling_price = Decimal(request.POST.get("selling_price") or 0)
        except (TypeError, ValueError):
            messages.error(request, "Please enter valid numeric values for quantity, cost, and selling price.")
            return render(request, "create_stock_receipt.html", {"products": products})

        if quantity_received <= 0:
            messages.error(request, "Quantity received must be a positive number.")
            return render(request, "create_stock_receipt.html", {"products": products})

        if unit_cost <= 0:
            messages.error(request, "Unit cost must be greater than zero.")
            return render(request, "create_stock_receipt.html", {"products": products})

        if selling_price <= 0:
            messages.error(request, "Selling price must be greater than zero.")
            return render(request, "create_stock_receipt.html", {"products": products})

        receipt = StockReceipt.objects.create(
            product=product,
            supplier_name=supplier_name,
            quantity_received=quantity_received,
            unit_cost=unit_cost,
            selling_price=selling_price,
            supplier_paid=request.POST.get("supplier_paid") == "on"
        )
        messages.success(request, "Stock receipt created successfully.")
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
        try:
            quantity_received = int(request.POST.get("quantity_received", 0))
            unit_cost = Decimal(request.POST.get("unit_cost") or 0)
            selling_price = Decimal(request.POST.get("selling_price") or 0)
        except (TypeError, ValueError):
            messages.error(request, "Please enter valid numeric values for quantity, cost, and selling price.")
            return render(request, "edit_stock_receipt.html", {
                "receipt": receipt,
                "products": products
            })

        if quantity_received <= 0:
            messages.error(request, "Quantity received must be a positive number.")
            return render(request, "edit_stock_receipt.html", {
                "receipt": receipt,
                "products": products
            })

        if unit_cost <= 0:
            messages.error(request, "Unit cost must be greater than zero.")
            return render(request, "edit_stock_receipt.html", {
                "receipt": receipt,
                "products": products
            })

        if selling_price <= 0:
            messages.error(request, "Selling price must be greater than zero.")
            return render(request, "edit_stock_receipt.html", {
                "receipt": receipt,
                "products": products
            })

        receipt.product = product
        receipt.supplier_name = request.POST.get("supplier_name")
        receipt.quantity_received = quantity_received
        receipt.unit_cost = unit_cost
        receipt.selling_price = selling_price
        receipt.supplier_paid = request.POST.get("supplier_paid") == "on"
        receipt.save()
        messages.success(request, "Stock receipt updated successfully.")
        return redirect("goods_received_note", receipt_id=receipt.id)

    return render(request, "edit_stock_receipt.html", {
        "receipt": receipt,
        "products": products
    })


def delete_stock_receipt(request, receipt_id):
    receipt = get_object_or_404(StockReceipt, id=receipt_id)

    if request.method == "POST":
        receipt.delete()
        messages.success(request, "Stock receipt deleted successfully.")
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

        total_sold = SaleItem.objects.filter(
            product=product
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

        total_sold = SaleItem.objects.filter(
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
            product.category_name.category_name,
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

def supplier_report(request):
    
    suppliers = StockReceipt.objects.values('supplier_name').distinct()
    
    report_data = []
    total_credit_owed = 0
    total_paid = 0
    
    for supplier in suppliers:
        supplier_name = supplier['supplier_name']
        

        receipts = StockReceipt.objects.filter(supplier_name=supplier_name)
        
        
        total_quantity = receipts.aggregate(Sum('quantity_received'))['quantity_received__sum'] or 0
        total_amount = receipts.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        
        paid_amount = receipts.filter(supplier_paid=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        
        credit_amount = receipts.filter(supplier_paid=False).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        
        credit_count = receipts.filter(supplier_paid=False).count()
        paid_count = receipts.filter(supplier_paid=True).count()
        
        
        last_receipt = receipts.order_by('-date_received').first()
        last_date = last_receipt.date_received.date() if last_receipt else None
        
        
        if credit_amount > 0 and paid_amount > 0:
            status = "Partially Paid"
        elif credit_amount > 0:
            status = "On Credit"
        else:
            status = "Fully Paid"
        
        report_data.append({
            'supplier_name': supplier_name,
            'total_quantity': total_quantity,
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'credit_amount': credit_amount,
            'credit_count': credit_count,
            'paid_count': paid_count,
            'last_date': last_date,
            'status': status,
        })
        
        total_credit_owed += credit_amount
        total_paid += paid_amount
    
    context = {
        'report_data': report_data,
        'total_credit_owed': total_credit_owed,
        'total_paid': total_paid,
        'total_suppliers': len(report_data),
    }
    
    return render(request, 'supplier_report.html', context)

