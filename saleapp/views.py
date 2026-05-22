from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from saleapp.models import Category, Product, Sales, SaleItem
from stockapp.models import StockReceipt
from django.db.models import Sum
from django.http import HttpResponse
from openpyxl import Workbook
from datetime import timedelta
from django.utils import timezone
from schemeapp.models import SchemeCustomer, SchemePayment


def home(request):
    all_sales = Sales.objects.all().order_by("-sale_date")
    total_money = all_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    return render(request, "home.html", {
        'sales': all_sales,
        'total_sales_value': total_money
    })



def category_list(request):
    categories = Category.objects.all()
    return render(request, "category_list.html", {'categories': categories})

def create_category(request):
    if request.method == "POST":
        name = request.POST.get('category_name')
        slug = request.POST.get('slug')
        if not name or not slug:
            messages.error(request, "Please provide both category name and slug.")
            return render(request, "create_category.html")

        Category.objects.create(category_name=name, slug=slug)
        messages.success(request, "Category created successfully.")
        return redirect('category_list')
    return render(request, "create_category.html")

def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted successfully.")
        return redirect('category_list')
    return render(request, "delete_category.html", {'category': category})

def product_list(request):
    products = Product.objects.all()
    return render(request, "product_list.html", {'products': products})

def create_product(request):
    categories = Category.objects.all()
    
    if request.method == "POST":
        cat = get_object_or_404(Category, id=request.POST.get('category'))
        product_name = request.POST.get('product_name')
        if not product_name:
            messages.error(request, "Product name is required.")
            return render(request, "create_product.html", {'categories': categories})

        try:
            cost_price = float(request.POST.get('cost_price', 0))
            unit_price = float(request.POST.get('unit_price', 0))
        except (TypeError, ValueError):
            messages.error(request, "Please enter valid numeric prices.")
            return render(request, "create_product.html", {'categories': categories})

        Product.objects.create(
            category_name=cat,
            product_name=product_name,
            cost_price=cost_price,
            unit_price=unit_price,
            description=request.POST.get('description', '')
        )
        messages.success(request, "Product created successfully.")
        return redirect('product_list')
    
    return render(request, "create_product.html", {'categories': categories})

def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    
    if request.method == "POST":
        cat = get_object_or_404(Category, id=request.POST.get('category'))
        product.category_name = cat
        product.product_name = request.POST.get('product_name')
        try:
            product.unit_price = float(request.POST.get('unit_price', 0))
        except (TypeError, ValueError):
            messages.error(request, "Please enter a valid selling price.")
            return render(request, "edit_product.html", {
                'product': product,
                'categories': categories
            })
        product.description = request.POST.get('description', '')
        product.save()
        messages.success(request, "Product updated successfully.")
        return redirect('product_list')
    
    return render(request, "edit_product.html", {
        'product': product,
        'categories': categories
    })

def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect('product_list')
    return render(request, "delete_product.html", {'product': product})


def _parse_sale_items(request):
    product_ids = request.POST.getlist('product')
    quantities = request.POST.getlist('quantity')
    items = []

    for product_id, quantity in zip(product_ids, quantities):
        if not product_id or not quantity:
            continue

        try:
            qty = int(quantity)
        except (TypeError, ValueError):
            raise ValueError("Please enter valid quantities for each product.")

        if qty <= 0:
            raise ValueError("Quantities must be greater than zero.")

        product = get_object_or_404(Product, id=product_id)
        items.append({'product': product, 'quantity': qty})

    if not items:
        raise ValueError("Please add at least one product to the sale.")

    return items


def _validate_order_stock(items):
    quantities_by_product = {}
    for item in items:
        quantities_by_product[item['product']] = quantities_by_product.get(item['product'], 0) + item['quantity']

    for product, required_qty in quantities_by_product.items():
        received = StockReceipt.objects.filter(product=product).aggregate(Sum('quantity_received'))['quantity_received__sum'] or 0
        sold = SaleItem.objects.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
        available = received - sold
        if required_qty > available:
            raise ValueError(f"Only {available} items available for {product.product_name}.")


def _calculate_order_total(items, distance):
    subtotal = sum(item['product'].unit_price * item['quantity'] for item in items)
    if distance <= 10 and subtotal >= 500000:
        transport_fee = 0
        transport_note = "Free delivery"
    else:
        transport_fee = 30000
        transport_note = "Standard delivery fee"
    return subtotal + transport_fee, transport_fee, transport_note


def create_sale(request):
    products = Product.objects.all()

    if request.method == "POST":
        customer_name = request.POST.get('customer_name', '').strip()

        try:
            items = _parse_sale_items(request)
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, "create_sale.html", {'products': products})

        try:
            distance = float(request.POST.get('distance', 0))
        except (TypeError, ValueError):
            messages.error(request, "Please enter a valid distance value.")
            return render(request, "create_sale.html", {'products': products})

        if distance <= 0:
            messages.error(request, "Distance must be greater than zero.")
            return render(request, "create_sale.html", {'products': products})

        try:
            _validate_order_stock(items)
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, "create_sale.html", {'products': products})

        total_amount, transport_fee, transport_note = _calculate_order_total(items, distance)
        total_quantity = sum(item['quantity'] for item in items)

        sale = Sales.objects.create(
            product_name=items[0]['product'],
            customer_name=customer_name or None,
            quantity=total_quantity,
            distance=distance,
            transport=transport_fee,
            transport_note=transport_note,
            total_amount=total_amount
        )

        for item in items:
            SaleItem.objects.create(
                sale=sale,
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['product'].unit_price,
                line_total=item['product'].unit_price * item['quantity']
            )

        messages.success(request, "Sale recorded successfully.")
        return redirect('invoice', sale_id=sale.id)

    return render(request, "create_sale.html", {'products': products})


def invoice(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    items = sale.items.all()
    return render(request, "invoice.html", {'sale': sale, 'items': items})


def edit_sale(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    products = Product.objects.all()
    existing_items = sale.items.all()

    if request.method == "POST":
        customer_name = request.POST.get('customer_name', '').strip()

        try:
            items = _parse_sale_items(request)
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, "edit_sale.html", {
                'sale': sale,
                'products': products,
                'items': existing_items
            })

        try:
            distance = float(request.POST.get('distance', 0))
        except (TypeError, ValueError):
            messages.error(request, "Please enter a valid distance value.")
            return render(request, "edit_sale.html", {
                'sale': sale,
                'products': products,
                'items': existing_items
            })

        if distance <= 0:
            messages.error(request, "Distance must be greater than zero.")
            return render(request, "edit_sale.html", {
                'sale': sale,
                'products': products,
                'items': existing_items
            })

        try:
            _validate_order_stock(items)
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, "edit_sale.html", {
                'sale': sale,
                'products': products,
                'items': existing_items
            })

        total_amount, transport_fee, transport_note = _calculate_order_total(items, distance)
        total_quantity = sum(item['quantity'] for item in items)

        sale.product_name = items[0]['product']
        sale.customer_name = customer_name or sale.customer_name
        sale.quantity = total_quantity
        sale.distance = distance
        sale.transport = transport_fee
        sale.transport_note = transport_note
        sale.total_amount = total_amount
        sale.save()

        sale.items.all().delete()
        for item in items:
            SaleItem.objects.create(
                sale=sale,
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['product'].unit_price,
                line_total=item['product'].unit_price * item['quantity']
            )

        messages.success(request, "Sale updated successfully.")
        return redirect('sales_report')

    return render(request, "edit_sale.html", {
        'sale': sale,
        'products': products,
        'items': existing_items
    })

def delete_sale(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    if request.method == "POST":
        sale.delete()
        messages.success(request, "Sale deleted successfully.")
        return redirect('home')
    return render(request, "delete_sale.html", {'sale': sale})


def sales_report(request):
    sales = Sales.objects.all().order_by('-sale_date')

    start = request.GET.get('start_date')
    end = request.GET.get('end_date')

    if start:
        sales = sales.filter(sale_date__date__gte=start)
    if end:
        sales = sales.filter(sale_date__date__lte=end)

    total_sales_amount = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_quantity_sold = sales.aggregate(Sum('quantity'))['quantity__sum'] or 0

    return render(request, "sales_report.html", {
        'sales': sales,
        'total_sales_amount': total_sales_amount,
        'total_quantity_sold': total_quantity_sold,
        'start_date': start,
        'end_date': end
    })


def export_sales_report_excel(request):
    sales = Sales.objects.all().order_by('-sale_date')

    start = request.GET.get('start_date')
    end = request.GET.get('end_date')

    if start and start != 'None':
        sales = sales.filter(sale_date__date__gte=start)
    if end and end != 'None':
        sales = sales.filter(sale_date__date__lte=end)

    wb = Workbook()
    ws = wb.active
    ws.title = "Sales"

    ws.append(['Invoice No', 'Customer', 'Products', 'Quantity', 'Transport', 'Total', 'Date'])

    for sale in sales:
        products_string = "; ".join([f"{item.product.product_name} x {item.quantity}" for item in sale.items.all()])
        ws.append([
            f"INV-{sale.id}",
            sale.customer_name or "Walk-in Customer",
            products_string,
            sale.quantity,
            sale.transport,
            sale.total_amount,
            sale.sale_date.strftime('%Y-%m-%d')
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sales.xlsx"'
    wb.save(response)
    return response


def dashboard(request):
    today = timezone.now().date()

    today_sales = Sales.objects.filter(sale_date__date=today)
    today_total = today_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    today_count = today_sales.count()

    total_products = Product.objects.count()
    low_stock_products = []
    low_stock_count = 0
    low_stock_count = len(low_stock_products)

    stock_value = 0
    for p in Product.objects.all():
        stock_value += p.unit_price * 100

    credit_customers = SchemeCustomer.objects.count()
    credit_balance = 0
    for customer in SchemeCustomer.objects.all():
        payments = SchemePayment.objects.filter(customer=customer)
        total_paid = sum(p.amount_paid for p in payments)
        credit_balance += total_paid
    
    
    weekly_sales = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        day_sales = Sales.objects.filter(sale_date__date=date)
        day_total = day_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        day_count = day_sales.count()
        
        weekly_sales.append({
            'day_name': date.strftime('%A'),
            'date': date,
            'order_count': day_count,
            'total': day_total,
            'average': day_total / day_count if day_count > 0 else 0,
        })
    
    context = {
        'today_sales': today_total,
        'today_count': today_count,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'stock_value': stock_value,
        'credit_balance': credit_balance,
        'credit_customers': credit_customers,
        'weekly_sales': weekly_sales,
    }
    
    return render(request, 'dashboard.html', context)

