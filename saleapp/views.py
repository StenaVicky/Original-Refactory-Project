from django.shortcuts import render, redirect, get_object_or_404
from saleapp.models import Category, Product, Sales
from django.db import IntegrityError
from stockapp.models import StockReceipt
from django.db.models import Sum
from django.http import HttpResponse
from openpyxl import Workbook

# Create your views here
def home(request):
    sales = Sales.objects.all().order_by("-sale_date")

    total_sales_value = sales.aggregate(
        total=Sum("total_price")
    )["total"] or 0

    return render(request, "home.html", {
        "sales": sales,
        "total_sales_value": total_sales_value
    })

def category_list(request):
    categories = Category.objects.all()
    return render(request, "category_list.html", {"categories": categories})


def create_category(request):
    if request.method == "POST":
        category_name = request.POST.get("category_name")
        slug = request.POST.get("slug")

        try:
            Category.objects.create(
                category_name=category_name,
                slug=slug
            )
            return redirect("category_list")

        except IntegrityError:
            return render(request, "create_category.html", {
                "error": "This category already exists."
            })

    return render(request, "create_category.html")


def product_list(request):
    products = Product.objects.all()
    return render(request, "product_list.html", {"products": products})


def create_product(request):
    categories = Category.objects.all()

    if request.method == "POST":
        category = get_object_or_404(Category, id=request.POST.get("category"))

        Product.objects.create(
            category_name=category,
            product_name=request.POST.get("product_name"),
            unit_price=0,
            description=request.POST.get("description")
        )

        return redirect("product_list")

    return render(request, "create_product.html", {
        "categories": categories
    })

def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.delete()
        return redirect("product_list")

    return render(request, "delete_product.html", {
        "product": product
    })


def create_sale(request):
    products = Product.objects.all()

    if request.method == "POST":
        product_id = request.POST.get("product")
        quantity = int(request.POST.get("quantity"))

        product = get_object_or_404(Product, id=product_id)

        # Calculate stock received
        total_received = StockReceipt.objects.filter(
            product=product
        ).aggregate(
            total=Sum("quantity_received")
        )["total"] or 0

        # Calculate stock already sold
        total_sold = Sales.objects.filter(
            product_name=product
        ).aggregate(
            total=Sum("quantity")
        )["total"] or 0

        # Current available stock
        available_stock = total_received - total_sold

        # Prevent selling more than available stock
        if quantity > available_stock:
            return render(request, "create_sale.html", {
                "products": products,
                "error": f"Not enough stock. Available stock is {available_stock}."
            })

        # Calculate total sale price
        total_price = product.unit_price * quantity

        # Save sale
        sale = Sales.objects.create(
            product_name=product,
            quantity=quantity,
            total_price=total_price
        )

        return redirect("invoice", sale_id=sale.id)

    return render(request, "create_sale.html", {
        "products": products
    })


def invoice(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    return render(request, "invoice.html", {"sale": sale})


def edit_sale(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    products = Product.objects.all()

    if request.method == "POST":
        product = get_object_or_404(Product, id=request.POST.get("product"))
        quantity = int(request.POST.get("quantity"))

        sale.product_name = product
        sale.quantity = quantity
        sale.total_price = product.unit_price * quantity
        sale.save()

        return redirect("invoice", sale_id=sale.id)

    return render(request, "edit_sale.html", {
        "sale": sale,
        "products": products
    })


def delete_sale(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)

    if request.method == "POST":
        sale.delete()
        return redirect("home")

    return render(request, "delete_sale.html", {"sale": sale})

def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()

    if request.method == "POST":
        category = get_object_or_404(Category, id=request.POST.get("category"))

        product.category_name = category
        product.product_name = request.POST.get("product_name")
        product.description = request.POST.get("description")
        product.save()

        return redirect("product_list")

    return render(request, "edit_product.html", {
        "product": product,
        "categories": categories
    })


def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        category.delete()
        return redirect("category_list")

    return render(request, "delete_category.html", {
        "category": category
    })

def sales_report(request):
    sales = Sales.objects.all().order_by("-sale_date")

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date:
        sales = sales.filter(sale_date__date__gte=start_date)

    if end_date:
        sales = sales.filter(sale_date__date__lte=end_date)

    total_sales_amount = sales.aggregate(
        total=Sum("total_price")
    )["total"] or 0

    total_quantity_sold = sales.aggregate(
        total=Sum("quantity")
    )["total"] or 0

    return render(request, "sales_report.html", {
        "sales": sales,
        "start_date": start_date,
        "end_date": end_date,
        "total_sales_amount": total_sales_amount,
        "total_quantity_sold": total_quantity_sold,
    })
    
def export_sales_report_excel(request):
    sales = Sales.objects.all().order_by("-sale_date")

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date and start_date != "None":
        sales = sales.filter(sale_date__date__gte=start_date)

    if end_date and end_date != "None":
        sales = sales.filter(sale_date__date__lte=end_date)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Sales Report"

    worksheet.append([
        "Product",
        "Category",
        "Unit Price",
        "Quantity",
        "Total Price",
        "Sale Date"
    ])

    for sale in sales:
        worksheet.append([
            sale.product_name.product_name,
            sale.product_name.category_name.category_name,
            sale.product_name.unit_price,
            sale.quantity,
            sale.total_price,
            sale.sale_date.strftime("%Y-%m-%d %H:%M"),
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="sales_report.xlsx"'

    workbook.save(response)
    return response