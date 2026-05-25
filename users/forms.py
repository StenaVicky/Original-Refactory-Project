from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


class PlainAuthenticationForm(AuthenticationForm):
    use_required_attribute = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field, "max_length"):
                field.max_length = None
            field.widget.attrs.pop("maxlength", None)
            field.widget.attrs.pop("required", None)


class UserRegistrationForm(UserCreationForm):
    use_required_attribute = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field, "max_length"):
                field.max_length = None
            field.widget.attrs.pop("maxlength", None)
            field.widget.attrs.pop("required", None)

    ROLE_CHOICES=(
        ('admin', 'Admin'),
        ('sales_manager', 'Sales_Manager'),
        ('stock_manager', 'Stock_Manager'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}))

    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}))

    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}))

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'role']
