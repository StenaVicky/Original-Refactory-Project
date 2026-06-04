from django.db import models
from django.db.models import Sum

# Create your models here.
class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.category_name


class Product(models.Model):
    category_name = models.ForeignKey(Category, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=100)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField()
    current_stock = models.IntegerField(default=0)  

    def __str__(self):
        return self.product_name

    @property
    def total_received(self):
        return self.stockreceipt_set.aggregate(Sum('quantity_received'))['quantity_received__sum'] or 0

    @property
    def total_sold(self):
        return self.saleitem_set.aggregate(Sum('quantity'))['quantity__sum'] or 0

class Sales(models.Model):
    product_name = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    distance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_note = models.CharField(max_length=255, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.product_name:
            return f"{self.product_name.product_name} - {self.quantity} units"
        return f"Order #{self.id} - {self.quantity} units"

    @property
    def total_items(self):
        total = self.items.aggregate(Sum('quantity'))['quantity__sum']
        return total or self.quantity

    @property
    def item_summary(self):
        items = self.items.all()
        if items.exists():
            return ", ".join(f"{item.product.product_name} ({item.quantity})" for item in items)
        if self.product_name:
            return self.product_name.product_name
        return "No products"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sales, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    distance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    

    def __str__(self):
        return f"{self.product.product_name} x {self.quantity}"