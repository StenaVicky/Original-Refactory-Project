
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from saleapp.models import Product, Sales
from schemeapp.models import SchemeCustomer, SchemePayment

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

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if username == "admin" and password == "admin123":
            return redirect("dashboard")
    return render(request, "login.html")

def logout(request):
    
    return render(request, 'logout.html')
       
           
    