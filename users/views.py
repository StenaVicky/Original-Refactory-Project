from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from django.contrib import messages
from .forms import UserRegistrationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy



# Create your views here.
def register(request):

    if request.method == 'POST':

        form = UserRegistrationForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            user.is_active = False
            user.save()

            role = form.cleaned_data.get('role')

            group = Group.objects.get(name=role)

            user.groups.add(group)

            messages.success(
                request,
                'Account created successfully. Wait for admin approval.'
            )

            return redirect('login')

    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})

class CustomLoginView(LoginView):

    template_name = 'registration/login.html'
    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password')
        return super().form_invalid(form)
    
    def get_success_url(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name='Admin').exists():
            return reverse_lazy('dashboard')
        if user.groups.filter(name='Sales Manager').exists():
            return reverse_lazy('home')
        if user.groups.filter(name='Stock Manager').exists():
            return reverse_lazy('stock_receipt_list')
        return reverse_lazy('login')
   
   
   