from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from saleapp.models import Category, Product, Sales, SaleItem
from django.db.models import Q, Sum
from django.http import HttpResponse
from openpyxl import Workbook
from datetime import timedelta
from django.utils import timezone
from schemeapp.models import SchemeCustomer, SchemePayment
from django.contrib.auth.decorators import login_required
from nyondoproject.form_messages import clean_form_errors, clean_message
from .forms import  ProductForm, SaleForm
from django.db import transaction




def home(request):
    search_query = request.GET.get('search', '').strip()
    all_sales = Sales.objects.all().order_by("-sale_date")

    if search_query:
        all_sales = all_sales.filter(
            Q(customer_name__icontains=search_query) |
            Q(items__product__product_name__icontains=search_query)
        )
        if search_query.isdigit():
            all_sales = all_sales | Sales.objects.filter(id=search_query)
        all_sales = all_sales.distinct().order_by("-sale_date")

    total_money = all_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    return render(request, "home.html", {
        'sales': all_sales,
        'total_sales_value': total_money,
        'search_query': search_query
    })


@login_required
def category_list(request):
    search_query = request.GET.get('search', '').strip()
    categories = Category.objects.all()

    if search_query:
        categories = categories.filter(
            Q(category_name__icontains=search_query) |
            Q(slug__icontains=search_query)
        )

    return render(request, "category_list.html", {
        'categories': categories,
        'search_query': search_query
    })



def create_category(request):
    if request.method == 'POST':
        # Get form data
        category_name = request.POST.get('category_name')
        slug = request.POST.get('slug')
        
        # Store data to repopulate form
        form_data = {
            'category_name': category_name,
            'slug': slug,
        }
        
        # Validation errors
        errors = {}
        
        # Category Name validation
        if not category_name:
            errors['category_name'] = 'Category name is required'
        elif len(category_name) < 2:
            errors['category_name'] = 'Category name must be at least 2 characters'
        elif len(category_name) > 100:
            errors['category_name'] = 'Category name must be less than 100 characters'
        
        # Slug validation
        if not slug:
            errors['slug'] = 'Slug is required'
        elif ' ' in slug:
            errors['slug'] = 'Slug cannot contain spaces. Use hyphens instead'
        elif not slug.replace('-', '').isalnum():
            errors['slug'] = 'Slug can only contain letters, numbers, and hyphens'
        
        # Checks if slug already exists 
        if not errors.get('slug') and slug:
            from .models import Category
            if Category.objects.filter(slug=slug).exists():
                errors['slug'] = 'This slug already exists. Please use a different slug'
        
        
        if errors:
            return render(request, 'create_category.html', {
                'errors': errors,
                'form_data': form_data,
            })
        
        # If validation passes, save to database
        try:
            Category = Category.objects.create(
                category_name=category_name,
                slug=slug,
            )
            messages.success(request, f'Category "{category_name}" created successfully!')
            return redirect('category_list')
        except Exception as e:
            messages.error(request, f'Error saving category: {str(e)}')
            return render(request, 'create_category.html', {
                'errors': {},
                'form_data': form_data,
            })
    
    else:
        # GET request - empty form
        return render(request, 'create_category.html', {
            'errors': {},
            'form_data': {},
        })
@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted successfully.")
        return redirect('category_list')
    return render(request, "delete_category.html", {'category': category})

@login_required
def product_list(request):
    search_query = request.GET.get('search', '').strip()
    products = Product.objects.all()

    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) |
            Q(category_name__category_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    return render(request, "product_list.html", {
        'products': products,
        'search_query': search_query
    })

@login_required
def create_product(request):
    categories = Category.objects.all()
    
    if request.method == "POST":
        category_id = request.POST.get('category', '').strip()
        product_name = request.POST.get('product_name', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Store form data to repopulate
        form_data = {
            'category': category_id,
            'product_name': product_name,
            'description': description,
        }
        
        errors = {}
        
        # Validate Category
        if not category_id:
            errors['category'] = "Category is required. Please select a category."
        else:
            if not Category.objects.filter(id=category_id).exists():
                errors['category'] = "Selected category does not exist."
        
        # Validate Product Name
        if not product_name:
            errors['product_name'] = "Product name is required. Please fill it in."
        elif len(product_name) < 2:
            errors['product_name'] = "Product name must be at least 2 characters."
        elif Product.objects.filter(product_name__iexact=product_name).exists():
            errors['product_name'] = "A product with this name already exists."
        
        # Validate Description 
        if description and len(description) < 3:
            errors['description'] = "Description must be at least 3 characters if provided."
        
        # If errors exist, show form with errors
        if errors:
            return render(request, 'create_product.html', {
                'categories': categories,
                'form_data': form_data,
                'errors': errors
            })
        
        # Save product
        try:
            category = Category.objects.get(id=category_id)
            product = Product.objects.create(
                category_name=category,
                product_name=product_name,
                description=description or "",
                unit_price=0  # Will be updated when stock is received
            )
            messages.success(request, f"✅ Product '{product_name}' added successfully!")
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f"Error saving product: {str(e)}")
            return render(request, 'create_product.html', {
                'categories': categories,
                'form_data': form_data,
                'errors': errors
            })
    
    # GET request - show empty form
    return render(request, 'create_product.html', {
        'categories': categories,
        'form_data': {},
        'errors': {}
    })
  
@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect('product_list')
        messages.error(request, clean_form_errors(form))
    
    return render(request, "edit_product.html", {
        'product': product,
        'categories': categories
    })


@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect('product_list')
    return render(request, "delete_product.html", {'product': product})


def _parse_sale_items(request):
    product_ids = request.POST.getlist('product[]')
    quantities = request.POST.getlist('quantity[]')
    items = []

    for product_id, quantity in zip(product_ids, quantities):
        if not product_id or not quantity:
            continue

        try:
            qty = int(quantity)
        except (TypeError, ValueError):
            raise ValueError("Please enter valid quantities for each product")

        if qty <= 0:
            raise ValueError("Quantities must be greater than zero")

        product = get_object_or_404(Product, id=product_id)
        items.append({'product': product, 'quantity': qty})

    if not items:
        raise ValueError("Please add at least one product to the sale")

    return items


def _available_stock(product, exclude_sale=None):
    sold_items = SaleItem.objects.filter(product=product)
    if exclude_sale:
        sold_items = sold_items.exclude(sale=exclude_sale)

    received = product.total_received
    sold = sold_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
    return received - sold


def _validate_order_stock(items, exclude_sale=None):
    quantities_by_product = {}
    for item in items:
        quantities_by_product[item['product']] = quantities_by_product.get(item['product'], 0) + item['quantity']

    for product, required_qty in quantities_by_product.items():
        if required_qty > _available_stock(product, exclude_sale):
            raise ValueError("Not enough stock available for selected product")


def _calculate_order_total(items, distance):
    subtotal = sum(item['product'].unit_price * item['quantity'] for item in items)
    if distance <= 10 and subtotal >= 500000:
        transport_fee = 0
        transport_note = "Free delivery"
    else:
        transport_fee = 30000
        transport_note = "Standard delivery fee"
    return subtotal + transport_fee, transport_fee, transport_note

@login_required

def create_sale(request):
    products = Product.objects.all()
    
    if request.method == "POST":
        form = SaleForm(request.POST)
        if not form.is_valid():
            messages.error(request, clean_form_errors(form))
            return render(request, "create_sale.html", {'products': products})
        
        customer_name = form.cleaned_data['customer_name'].strip()
        distance = form.cleaned_data['distance']
        
        try:
            items = _parse_sale_items(request)
            _validate_order_stock(items)
            total_amount, transport_fee, transport_note = _calculate_order_total(items, distance)
            
            sale = Sales.objects.create(
                product_name=items[0]['product'],
                customer_name=customer_name or None,
                quantity=sum(item['quantity'] for item in items),
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
            
            messages.success(request, f"Sale #{sale.id} created successfully!")
            return redirect('home')
        
        except ValueError as exc:
            messages.error(request, clean_message(exc))
            return render(request, "create_sale.html", {'products': products})
    
    return render(request, "create_sale.html", {'products': products})
def edit_sale(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    products = Product.objects.all()
    items = sale.items.all()
    
    if request.method == "POST":
        errors = {}
        
        # Distance validation
        try:
            distance = float(request.POST.get('distance', ''))
            if distance < 0:
                errors['distance'] = "Distance cannot be negative."
        except ValueError:
            errors['distance'] = "Distance must be a valid number."
        
        # Process items
        valid_items = []
        old = {i.product.id: i.quantity for i in items}
        
        for pid, qty in zip(request.POST.getlist('product[]'), request.POST.getlist('quantity[]')):
            if not pid or not qty:
                continue
            try:
                p = Product.objects.get(id=pid)
                q = int(qty)
                if q > 0 and q <= (p.current_stock + old.get(p.id, 0)):
                    valid_items.append({'product': p, 'quantity': q, 'subtotal': p.unit_price * q})
                else:
                    messages.error(request, f"Invalid quantity for {p.product_name}")
            except (ValueError, Product.DoesNotExist):
                pass
        
        if not valid_items:
            messages.error(request, "At least one valid product required.")
        elif not errors:
            with transaction.atomic():
                sale.customer_name = request.POST.get('customer_name', '').strip() or None
                sale.distance = float(request.POST.get('distance', 0))
                
                # Restore old stock
                for i in items:
                    i.product.current_stock += i.quantity
                    i.product.save()
                
                # Update items
                sale.items.all().delete()
                total = 0
                for v in valid_items:
                    SaleItem.objects.create(sale=sale, product=v['product'], quantity=v['quantity'], unit_price=v['product'].unit_price, line_total=v['subtotal'])
                    v['product'].current_stock -= v['quantity']
                    v['product'].save()
                    total += v['subtotal']
                
                sale.total_amount = total
                sale.save()
            
            messages.success(request, f"Sale #{sale.id} updated!")
            return redirect('sales_report')
        
        if errors:
            return render(request, 'edit_sale.html', {'sale': sale, 'products': products, 'items': items, 'errors': errors})
    
    return render(request, 'edit_sale.html', {'sale': sale, 'products': products, 'items': items, 'errors': {}})
@login_required
def invoice(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    items = sale.items.all()
    subtotal = sum(item.line_total for item in items)
    return render(request, "invoice.html", {
        'sale': sale,
        'items': items,
        'subtotal': subtotal,
    })

# The delete_sale view is now protected with @login_required to ensure only authenticated users can delete sales records.
@login_required
def delete_sale(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    if request.method == "POST":
        sale.delete()
        messages.success(request, "Sale deleted successfully.")
        return redirect('home')
    return render(request, "delete_sale.html", {'sale': sale})

@login_required
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

@login_required
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

@login_required
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
    

