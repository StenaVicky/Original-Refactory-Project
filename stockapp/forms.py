from django import forms
from .models import StockReceipt, Product

class StockReceiptForm(forms.ModelForm):
    class Meta:
        model = StockReceipt
        fields = ['product', 'supplier_name', 'quantity_received', 'unit_cost', 'selling_price', 'supplier_paid']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity_received': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'supplier_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_quantity_received(self):
        qty = self.cleaned_data.get('quantity_received')
        if not qty or qty <= 0:
            raise forms.ValidationError('Quantity must be > 0')
        return qty
    
    def clean_unit_cost(self):
        cost = self.cleaned_data.get('unit_cost')
        if not cost or cost <= 0:
            raise forms.ValidationError('Unit cost must be > 0')
        return cost
    
    def clean_selling_price(self):
        price = self.cleaned_data.get('selling_price')
        cost = self.cleaned_data.get('unit_cost')
        if not price or price <= 0:
            raise forms.ValidationError('Selling price must be > 0')
        if cost and price < cost:
            raise forms.ValidationError('Selling price cannot be less than unit cost')
        return price
    
    def clean_supplier_name(self):
        name = self.cleaned_data.get('supplier_name')
        if not name or len(name) < 3:
            raise forms.ValidationError('Supplier name must be at least 3 characters')
        return name


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'category_name', 'unit_price', 'cost_price', 'description']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category_name': forms.Select(attrs={'class': 'form-select'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean_product_name(self):
        name = self.cleaned_data.get('product_name')
        if not name or len(name) < 3:
            raise forms.ValidationError('Product name must be at least 3 characters')
        return name
    
    def clean_unit_price(self):
        price = self.cleaned_data.get('unit_price')
        if not price or price <= 0:
            raise forms.ValidationError('Unit price must be > 0')
        return price