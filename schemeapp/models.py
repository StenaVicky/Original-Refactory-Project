from django.db import models 
from django.utils import timezone
from saleapp.models import Sales, Product
# from django.core.validators import RegexValidator


# Create your models here.
class SchemeCustomer(models.Model):
    full_name = models.CharField(max_length=255)
    nin_number = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    occupation = models.CharField(max_length=255)
    employer_name = models.CharField(max_length=255)
    payment_plan = models.CharField(max_length=255, blank=True, null=True)
    date_registered = models.DateField(default=timezone.now)
     
    def __str__(self):
        return self.full_name
    
class SchemePayment(models.Model):
    customer = models.ForeignKey(SchemeCustomer, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.customer.full_name} - {self.amount_paid} on {self.payment_date}"
    
class SchemeGoodsPickup(models.Model):
    customer = models.ForeignKey(SchemeCustomer, on_delete=models.CASCADE)
    product= models.ForeignKey( Product, on_delete=models.CASCADE)
    quantity_taken = models.PositiveIntegerField()
    linked_sale = models.ForeignKey(Sales, on_delete=models.SET_NULL, null=True, blank=True)
    pickup_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.full_name} - {self.product} ({self.quantity_taken}) on {self.pickup_date}"
    from django.db import models


