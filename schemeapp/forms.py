from django import forms
from saleapp.models import Product
from .models import SchemeCustomer
import re


class PlainFormMixin:
    use_required_attribute = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            for attr in ("max_length", "min_length", "min_value", "max_value"):
                if hasattr(field, attr):
                    setattr(field, attr, None)
            for attr in ("maxlength", "minlength", "min", "max", "step", "required"):
                field.widget.attrs.pop(attr, None)


class SchemeCustomerForm(PlainFormMixin, forms.ModelForm):
    class Meta:
        model = SchemeCustomer
        fields = '__all__'
    
    def clean_full_name(self):
        name = self.cleaned_data.get('full_name')
        if not name or len(name) < 3 or not re.match(r'^[A-Za-z\s]+$', name):
            raise forms.ValidationError('Name must use letters only')
        return name
    
    def clean_nin_number(self):
        nin = self.cleaned_data.get('nin_number', '').upper()
        if not nin or not re.match(r'^[A-Z0-9]{14}$', nin):
            raise forms.ValidationError('Enter a valid NIN')
        if SchemeCustomer.objects.filter(nin_number=nin).exists():
            raise forms.ValidationError('NIN already exists')
        return nin
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone or not re.match(r'^(07[0-9]{8}|\+256[0-9]{9}|256[0-9]{9})$', phone):
            raise forms.ValidationError('Enter a valid Ugandan phone number')
        if SchemeCustomer.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError('Phone already exists')
        return phone
    
    def clean_address(self):
        address = self.cleaned_data.get('address')
        if not address or len(address) < 5:
            raise forms.ValidationError('Address must be more descriptive')
        return address


class SchemePaymentForm(PlainFormMixin, forms.Form):
    amount_paid = forms.DecimalField(
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        widget=forms.TextInput,
        error_messages={
            "invalid": "Enter a valid payment amount",
            "min_value": "Payment amount must be greater than zero",
            "required": "Payment amount is required",
        },
    )
    notes = forms.CharField(required=False)


class SchemeGoodsPickupForm(PlainFormMixin, forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.none())
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.TextInput,
        error_messages={
            "invalid": "Enter a valid quantity",
            "min_value": "Quantity must be greater than zero",
            "required": "Quantity is required",
        },
    )

    def __init__(self, *args, products=None, **kwargs):
        super().__init__(*args, **kwargs)
        if products is not None:
            self.fields['product'].queryset = products
