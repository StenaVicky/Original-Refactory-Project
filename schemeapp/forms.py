from django import forms
from .models import SchemeCustomer
import re

class SchemeCustomerForm(forms.ModelForm):
    class Meta:
        model = SchemeCustomer
        fields = '__all__'
    
    def clean_full_name(self):
        name = self.cleaned_data.get('full_name')
        if not name or len(name) < 3 or not re.match(r'^[A-Za-z\s]+$', name):
            raise forms.ValidationError('Name must be 3+ letters only')
        return name
    
    def clean_nin_number(self):
        nin = self.cleaned_data.get('nin_number', '').upper()
        if not nin or not re.match(r'^[A-Z0-9]{14}$', nin):
            raise forms.ValidationError('NIN must be 14 uppercase letters/numbers')
        if SchemeCustomer.objects.filter(nin_number=nin).exists():
            raise forms.ValidationError('NIN already exists')
        return nin
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone or not re.match(r'^(07[0-9]{8}|\+256[0-9]{9}|256[0-9]{9})$', phone):
            raise forms.ValidationError('Phone must be 07xxxxxxxx or +256xxxxxxxxx and 10 digits')
        if SchemeCustomer.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError('Phone already exists')
        return phone
    
    def clean_address(self):
        address = self.cleaned_data.get('address')
        if not address or len(address) < 5:
            raise forms.ValidationError('Address must be at least 5 characters')
        return address