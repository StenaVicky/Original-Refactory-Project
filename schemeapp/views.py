from django.shortcuts import render,redirect,get_object_or_404
from .models import SchemeCustomer, SchemePayment, SchemeGoodsPickup
from saleapp.models import Product, Sales, SaleItem
from django.db.models import Q, Sum
from stockapp.models import StockReceipt
from django.contrib import messages
# from django.contrib.auth.decorators import login_required
from nyondoproject.form_messages import clean_form_errors
from .forms import SchemeCustomerForm, SchemePaymentForm, SchemeGoodsPickupForm



# Create your views here.
# @login_required
def scheme_customer_list(request):
    search_query = request.GET.get('search', '').strip()
    customers = SchemeCustomer.objects.all().order_by("-date_registered")

    if search_query:
        customers = customers.filter(
            Q(full_name__icontains=search_query) |
            Q(nin_number__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(employer_name__icontains=search_query)
        )

    return render(request, 'scheme_customer_list.html', {
        'customers': customers,
        'search_query': search_query
    })

# @login_required

def register_scheme_customer(request):
    if request.method == 'POST':
        form = SchemeCustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer registered successfully!')
            return redirect('scheme_customer_list')
        messages.error(request, clean_form_errors(form))
    else:
        form = SchemeCustomerForm()
    
    return render(request, 'register_scheme_customer.html', {'form': form})

# @login_required
def record_scheme_payment(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)
    if request.method == 'POST':
        form = SchemePaymentForm(request.POST)
        if form.is_valid():
            payment = SchemePayment.objects.create(customer=customer, **form.cleaned_data)
            messages.success(request, "Payment recorded successfully.")
            return redirect("temporary_receipt", payment_id=payment.id)
        messages.error(request, clean_form_errors(form))
    return render(request, "record_scheme_payment.html", {"customer": customer})

# @login_required
def temporary_receipt(request, payment_id):
    payment = get_object_or_404(SchemePayment,id=payment_id)
    return render(request,"temporary_receipt.html",{"payment":payment})

# @login_required
def customer_scheme_detail(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)
    payments = SchemePayment.objects.filter(customer=customer)
    pickups = SchemeGoodsPickup.objects.filter(customer=customer)
    total_paid = sum(payment.amount_paid for payment in payments)
    total_goods_value = sum(
      pickup.quantity_taken * pickup.product.unit_price for pickup in pickups  
    )
    balance = total_paid - total_goods_value

    return render(request,'customer_scheme_detail.html', {
        'customer': customer,
        'payments': payments,
        'pickups': pickups,
        "total_paid": total_paid,
        "total_goods_value": total_goods_value,
        'balance': balance,
    })

# @login_required
def scheme_goods_pickup(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)
    products = Product.objects.filter(
        category_name__category_name__in=[
            "Cement",
            "Iron sheets",
            "Iron bars",
        ]
    )
    
    if request.method == "POST":
        form = SchemeGoodsPickupForm(request.POST, products=products)
        if not form.is_valid():
            messages.error(request, clean_form_errors(form))
            return render(request, "scheme_goods_pickup.html", {
                "customer": customer,
                "products": products
            })

        product = form.cleaned_data['product']
        quantity = form.cleaned_data['quantity']
        total_received = StockReceipt.objects.filter(product=product).aggregate(total=Sum('quantity_received'))['total'] or 0
        total_sold = SaleItem.objects.filter(product=product).aggregate(total=Sum("quantity"))["total"] or 0
        available_stock = total_received - total_sold

        if quantity > available_stock:
            messages.error(request, "Not enough stock available")
            return render(request, "scheme_goods_pickup.html", {
                "customer": customer,
                "products": products
            })

        total_price = product.unit_price * quantity
    
        sale = Sales.objects.create(
            product_name=product,
            quantity=quantity,
            total_amount=total_price,
        )

        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=quantity,
            unit_price=product.unit_price,
            line_total=total_price
        )

        SchemeGoodsPickup.objects.create(
            customer=customer,  
            product=product,
            quantity_taken=quantity,
            linked_sale=sale
        )
        messages.success(request, "Goods pickup recorded successfully.")
        return redirect("invoice", sale_id=sale.id)
    return render(request, "scheme_goods_pickup.html",{
                 
         "customer": customer,
         "products": products
   })
def delete_customer(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)
    if request.method == 'POST':
        customer.delete()
        return redirect('scheme_customer_list')
    return render(request, 'delete_customer.html', {'customer': customer})

# @login_required
def customer_report(request):
    customers = SchemeCustomer.objects.all()
    
    customer_data = []
    total_deposits = 0
    total_withdrawn = 0
    total_balance = 0
    
    for customer in customers:
        payments = SchemePayment.objects.filter(customer=customer)
        total_deposited = sum(p.amount_paid for p in payments)
        
        pickups = SchemeGoodsPickup.objects.filter(customer=customer)
        total_withdrawn_amount = sum(p.quantity_taken * p.product.unit_price for p in pickups)
        
        balance = total_deposited - total_withdrawn_amount
        
        customer_data.append({
            'name': customer.full_name,
            'phone': customer.phone_number,
            'total_deposited': total_deposited,
            'total_withdrawn': total_withdrawn_amount,
            'balance': balance,
        })
        
        total_deposits += total_deposited
        total_withdrawn += total_withdrawn_amount
        total_balance += balance
    
    context = {
        'customers': customer_data,
        'total_customers': len(customer_data),
        'total_deposits': total_deposits,
        'total_withdrawn': total_withdrawn,
        'total_balance': total_balance,
    }
    
    return render(request, 'customer_report.html', context) 
