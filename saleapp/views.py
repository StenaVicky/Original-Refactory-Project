from django.shortcuts import render, redirect, get_object_or_404
from saleapp.models import Category, Product, Sales
from stockapp.models import StockReceipt
from django.db.models import Sum
from django.http import HttpResponse
from openpyxl import Workbook
from datetime import date, timedelta


def home(request):
    all_sales = Sales.objects.all().order_by("-sale_date")
    total_money = all_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    return render(request, "home.html", {
        'sales': all_sales,
        'total_sales_value': total_money
    })


def dashboard(request):
    # Today
    today_sales = Sales.objects.filter(sale_date__date=date.today())
    today_total = today_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # This week
    week_ago = date.today() - timedelta(days=7)
    week_sales = Sales.objects.filter(sale_date__date__gte=week_ago)
    week_total = week_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # All time
    all_sales = Sales.objects.all()
    all_total = all_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    return render(request, "dashboard.html", {
        'today_total': today_total,
        'week_total': week_total,
        'all_total': all_total
    })


def category_list(request):
    categories = Category.objects.all()
    return render(request, "category_list.html", {'categories': categories})

def create_category(request):
    if request.method == "POST":
        name = request.POST.get('category_name')
        slug = request.POST.get('slug')
        Category.objects.create(category_name=name, slug=slug)
        return redirect('category_list')
    return render(request, "create_category.html")

def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        category.delete()
        return redirect('category_list')
    return render(request, "delete_category.html", {'category': category})

def product_list(request):
    products = Product.objects.all()
    return render(request, "product_list.html", {'products': products})

def create_product(request):
    categories = Category.objects.all()
    
    if request.method == "POST":
        cat = get_object_or_404(Category, id=request.POST.get('category'))
        Product.objects.create(
            category_name=cat,
            product_name=request.POST.get('product_name'),
            unit_price=request.POST.get('unit_price', 0),
            description=request.POST.get('description', '')
        )
        return redirect('product_list')
    
    return render(request, "create_product.html", {'categories': categories})

def edit_product(request, id):
    product = get_object_or_404(Product, id=id)
    categories = Category.objects.all()
    
    if request.method == "POST":
        cat = get_object_or_404(Category, id=request.POST.get('category'))
        product.category_name = cat
        product.product_name = request.POST.get('product_name')
        product.unit_price = request.POST.get('unit_price', 0)
        product.description = request.POST.get('description', '')
        product.save()
        return redirect('product_list')
    
    return render(request, "edit_product.html", {
        'product': product,
        'categories': categories
    })

def delete_product(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == "POST":
        product.delete()
        return redirect('product_list')
    return render(request, "delete_product.html", {'product': product})


def create_sale(request):
    products = Product.objects.all()
    
    if request.method == "POST":
        # Get form data
        product = get_object_or_404(Product, id=request.POST.get('product'))
        qty = int(request.POST.get('quantity'))
        distance = float(request.POST.get('distance', 0))
        
       
        product_total = product.unit_price * qty
        
        
        if distance <= 10 and product_total >= 500000:
            transport_fee = 0
            transport_note = "Free delivery"
        else:
            transport_fee = 30000
            transport_note = "Standard delivery fee"
        
        
        received = StockReceipt.objects.filter(product=product).aggregate(Sum('quantity_received'))['quantity_received__sum'] or 0
        sold = Sales.objects.filter(product_name=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
        available = received - sold
        
        if qty > available:
            return render(request, "add_sale.html", {
                'products': products,
                'error': f'Only {available} items available'
            })
        
        
        sale = Sales.objects.create(
            product_name=product,
            quantity=qty,
            distance=distance,
            transport=transport_fee,
            transport_note=transport_note,
            total_amount=product_total
        )
        
        return redirect('view_invoice', sale_id=sale.id)
    
    return render(request, "create_sale.html", {'products': products})

def invoice(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    return render(request, "invoice.html", {'sale': sale})

def edit_sale(request, id):
    sale = get_object_or_404(Sales, id=id)
    products = Product.objects.all()
    
    if request.method == "POST":
        product = get_object_or_404(Product, id=request.POST.get('product'))
        qty = int(request.POST.get('quantity'))
        distance = float(request.POST.get('distance', 0))
        
        product_total = product.unit_price * qty
        
        if distance <= 10 and product_total >= 500000:
            transport_fee = 0
            note = "Free delivery"
        else:
            transport_fee = 30000
            note = "Standard delivery fee"
        
        sale.product_name = product
        sale.quantity = qty
        sale.distance = distance
        sale.transport = transport_fee
        sale.transport_note = note
        sale.total_amount = product_total
        sale.save()
        
        return redirect('view_invoice', sale_id=sale.id)
    
    return render(request, "edit_sale.html", {
        'sale': sale,
        'products': products
    })

def delete_sale(request, id):
    sale = get_object_or_404(Sales, id=id)
    if request.method == "POST":
        sale.delete()
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
    
    total = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_qty = sales.aggregate(Sum('quantity'))['quantity__sum'] or 0
    
    return render(request, "sales_report.html", {
        'sales': sales,
        'total_amount': total,
        'total_quantity': total_qty,
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
    
    
    ws.append(['Product', 'Quantity', 'Distance', 'Transport', 'Total', 'Date'])
    
    
    for sale in sales:
        ws.append([
            sale.product_name.product_name,
            sale.quantity,
            sale.distance,
            sale.transport,
            sale.total_amount,
            sale.sale_date.strftime('%Y-%m-%d')
        ])
   
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sales.xlsx"'
    wb.save(response)
    return response