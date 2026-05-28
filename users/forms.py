from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import  UserCreationForm




class UserRegistrationForm(UserCreationForm):
    ROLE_CHOICES=(
        ('Admin', 'Admin'),
        ('Sales Manager', 'Sales Manager'),
        ('Stock Manager', 'Stock Manager'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}))

    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}))

    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}))

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'role']
