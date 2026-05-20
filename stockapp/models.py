from django.db import models
from saleapp.models import Product


# Create your models here.
class StockReceipt(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier_name = models.CharField(max_length=100)
    quantity_received = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=50,decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=50, decimal_places=2,default=0)
    total_amount =models.DecimalField(max_digits=50, decimal_places=2, default=0)
    supplier_paid = models.BooleanField(default=False)
    date_received = models.DateTimeField(auto_now_add=True)
    re_order_level = models.IntegerField(default=10)

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity_received * self.unit_cost
        self.product.cost_price= self.unit_cost

        self.product.unit_price = self.selling_price
        self.product.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.quantity_received}"

