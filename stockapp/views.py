from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from saleapp.models import Product
from .models import StockReceipt
from django.http import HttpResponse
from openpyxl import Workbook
from django.contrib.auth.decorators import login_required
from nyondoproject.form_messages import clean_form_errors
from .forms import StockReceiptForm
from users.decorators import admin_required


@login_required
def stock_receipt_list(request):
    receipts = StockReceipt.objects.all().order_by("-date_received")
    return render(request, "stock_receipt_list.html", {
        "receipts": receipts
    })

@login_required
def create_stock_receipt(request):
    products = Product.objects.all()
    
    if request.method == "POST":
        # Get form data
        product_id = request.POST.get('product', '').strip()
        supplier_name = request.POST.get('supplier_name', '').strip()
        quantity_received = request.POST.get('quantity_received', '').strip()
        unit_cost = request.POST.get('unit_cost', '').strip()
        selling_price = request.POST.get('selling_price', '').strip()
        supplier_paid = request.POST.get('supplier_paid') == 'on'
        
        # Store submitted data
        form_data = {
            'product': product_id,
            'supplier_name': supplier_name,
            'quantity_received': quantity_received,
            'unit_cost': unit_cost,
            'selling_price': selling_price,
            'supplier_paid': supplier_paid,
        }
        
        errors = {}
        
        # Validate Product
        if not product_id:
            errors['product'] = "Product is required. Please fill it in."
        
        # Validate Supplier Name
        if not supplier_name:
            errors['supplier_name'] = "Supplier name is required. Please fill it in."
        
        # Validate Quantity Received
        if not quantity_received:
            errors['quantity_received'] = "Quantity received is required. Please fill it in."
        else:
            try:
                qty = int(quantity_received)
                if qty <= 0:
                    errors['quantity_received'] = "Quantity must be greater than 0."
            except ValueError:
                errors['quantity_received'] = "Quantity must be a valid number."
        
        # Validate Unit Cost
        if not unit_cost:
            errors['unit_cost'] = "Unit cost is required. Please fill it in."
        else:
            try:
                cost = float(unit_cost)
                if cost <= 0:
                    errors['unit_cost'] = "Unit cost must be greater than 0."
            except ValueError:
                errors['unit_cost'] = "Unit cost must be a valid number."
        
        # Validate Selling Price
        if not selling_price:
            errors['selling_price'] = "Selling price is required. Please fill it in."
        else:
            try:
                price = float(selling_price)
                if price <= 0:
                    errors['selling_price'] = "Selling price must be greater than 0."
            except ValueError:
                errors['selling_price'] = "Selling price must be a valid number."
        
        # If errors exist, show form with errors
        if errors:
            return render(request, 'create_stock_receipt.html', {
                'products': products,
                'form_data': form_data,
                'errors': errors
            })
        
        # Save to database
        try:
            product = Product.objects.get(id=product_id)
            
            # Update product prices and stock
            old_unit_cost = product.unit_cost if hasattr(product, 'unit_cost') else None
            
            # Create stock receipt
            receipt = StockReceipt.objects.create(
                product=product,
                supplier_name=supplier_name,
                quantity_received=int(quantity_received),
                unit_cost=float(unit_cost),
                selling_price=float(selling_price),
                supplier_paid=supplier_paid
            )
            
            # Update product's cost and selling price
            product.unit_cost = float(unit_cost)  # If you have unit_cost field
            product.unit_price = float(selling_price)  # Selling price
            product.current_stock += int(quantity_received)
            product.save()
            
            messages.success(request, f"Stock receipt added successfully! Added {quantity_received} units of {product.product_name}")
            return redirect('stock_receipt_list')
            
        except Product.DoesNotExist:
            errors['product'] = "Selected product does not exist."
            return render(request, 'create_stock_receipt.html', {
                'products': products,
                'form_data': form_data,
                'errors': errors
            })
        except Exception as e:
            messages.error(request, f"Error saving receipt: {str(e)}")
            return render(request, 'create_stock_receipt.html', {
                'products': products,
                'form_data': form_data,
                'errors': errors
            })
    
    # GET request - show empty form
    return render(request, 'create_stock_receipt.html', {
        'products': products,
        'form_data': {},
        'errors': {}
    })
@login_required
def goods_received_note(request, receipt_id):
    receipt = get_object_or_404(StockReceipt, id=receipt_id)

    return render(request, "goods_received_note.html", {
        "receipt": receipt
    })

@login_required
def edit_stock_receipt(request, receipt_id):
    receipt = get_object_or_404(StockReceipt, id=receipt_id)
    products = Product.objects.all()

    if request.method == "POST":
        form = StockReceiptForm(request.POST, instance=receipt)
        if form.is_valid():
            form.save()
            messages.success(request, "Stock receipt updated successfully.")
            return redirect("goods_received_note", receipt_id=receipt.id)
        messages.error(request, clean_form_errors(form))

    return render(request, "edit_stock_receipt.html", {
        "receipt": receipt,
        "products": products
    })

@login_required
@admin_required
def delete_stock_receipt(request, receipt_id):
    receipt = get_object_or_404(StockReceipt, id=receipt_id)

    if request.method == "POST":
        receipt.delete()
        messages.success(request, "Stock receipt deleted successfully.")
        return redirect("stock_receipt_list")

    return render(request, "delete_stock_receipt.html", {
        "receipt": receipt
    })

@login_required
def stock_report(request):
    products = Product.objects.all()
    report = []

    for product in products:
        current_stock = product.total_received - product.total_sold

        if current_stock <= 10:
            status = "Low Stock"
        elif current_stock <= 20:
            status = "Medium Stock"
        else:
            status = "High Stock"

        report.append({
            "product": product,
            "total_received": product.total_received,
            "total_sold": product.total_sold,
            "current_stock": current_stock,
            "status": status,
        })

    return render(request, "stock_report.html", {
        "report": report
    })

@login_required
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
        current_stock = product.current_stock

        if current_stock <= 5:
            status = "Low Stock"
        elif current_stock <= 20:
            status = "Medium Stock"
        else:
            status = "High Stock"

        worksheet.append([
            product.product_name,
            product.category_name.category_name,
            product.total_received,
            product.total_sold,
            current_stock,
            status
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = 'attachment; filename="stock_report.xlsx"'

    workbook.save(response)

    return response

@login_required
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

