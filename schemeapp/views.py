from django.shortcuts import render,redirect,get_object_or_404
from .models import SchemeCustomer, SchemePayment, SchemeGoodsPickup
from saleapp.models import Product, Sales
from django.db.models import Sum
from stockapp.models import StockReceipt
from django.utils import timezone
from django.contrib import messages


# Create your views here.
def scheme_customer_list(request):
    customers = SchemeCustomer.objects.all()
    return render(request, 'scheme_customer_list.html', {'customers': customers})


def register_scheme_customer(request):
    if request.method == 'POST':
        nin_number = request.POST.get('nin_number')

        phone_number = request.POST.get('phone_number')
        if not phone_number.startswith(('0', '+256', '256')):
            messages.error(request, "Phone number must start with 0, +256, or 256.")
            return render(request, 'register_scheme_customer.html')
        
        if SchemeCustomer.objects.filter(phone_number=phone_number).exists():
            messages.error(request, "A customer with this phone number already exists.")
            return render(request, 'register_scheme_customer.html')
        

        if SchemeCustomer.objects.filter(nin_number=nin_number).exists():
            messages.error(request, "A customer with this NIN number already exists.")
            return render(request, 'register_scheme_customer.html')
        SchemeCustomer.objects.create(
            full_name=request.POST.get('full_name'),
            nin_number=request.POST.get('nin_number'),
            phone_number=request.POST.get('phone_number'),
            address=request.POST.get('address'),
            occupation=request.POST.get('occupation'),
            employer_name=request.POST.get('employer_name'),
            payment_plan=request.POST.get('payment_plan'),
            date_registered=timezone.now(),
        )
        # messages.success(request, "Customer registered successfully.")
        
        return redirect('scheme_customer_list')
    return render(request, 'register_scheme_customer.html')


def record_scheme_payment(request, customer_id):
    customer =get_object_or_404(SchemeCustomer, id=customer_id)
    if request.method =='POST':
        SchemePayment.objects.create(
            customer=customer,
            amount_paid=request.POST.get('amount_paid'),
            
        )
        return redirect('scheme_customer_list')
    return render(request, "record_scheme_payment.html",{"customer":customer})

def temporary_receipt(request, payment_id):
    payment = get_object_or_404(SchemePayment,id=payment_id)
    return render(request,"temporary_receipt.html",{"payment":payment})

def customer_scheme_detail(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)
    payments = SchemePayment.objects.filter(customer=customer)
    pickups = SchemeGoodsPickup.objects.filter(customer=customer)
    total_paid = sum(payment.amount_paid for payment in payments)
    total_goods_value = 0
    for pickup in pickups:
        total_goods_value += pickup.quantity_taken * pickup.product.unit_price

    balance = total_paid - total_goods_value
    return render(request,'customer_scheme_detail.html', {
        'customer': customer,
        'payments': payments,
        'pickups': pickups,
        "total_paid": total_paid,
        "total_goods_value": total_goods_value,
        'balance': balance,
    })

def scheme_goods_pickup(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)
    products = Product.objects.filter(
        category_name__category_name__in=[
            "Cement",
            "Iron Sheets",
            "Bars",
        ]
    )
    if  request.method == "POST":
        product = get_object_or_404(Product, id=request.POST.get("product_id"))
        quantity = int(request.POST.get("quantity"))
        total_received = StockReceipt.objects.filter(
            product=product
        ).aggregate(total=Sum("quantity_received"))["total"] or 0
        total_sold = Sales.objects.filter(
            product_name=product
        ).aggregate(total=Sum("quantity"))["total"] or 0
        available_stock = total_received - total_sold
        if quantity > available_stock:
            return render(request, "schemeapp/scheme_goods_pickup.html", {
                "customer": customer,
                "products": product,
                "error": f"Not enough stock.Available stock is { available_stock }."
            })
        total_price = product.selling_price * quantity

        sale = Sales.objects.create(
            product_name=product,
            quantity=quantity,
            unit_selling_price=product.selling_price,
            total_amount=total_price,
            
        )

        SchemeGoodsPickup.objects.create(
            customer=customer,  
            product=product,
            quantity_taken=quantity,
            linked_sale=sale
        )
        return redirect("invoice", sale_id=sale.id)
    return render(request, "scheme_goods_pickup.html",{
                 
         "customer": customer,
         "products": products
   })