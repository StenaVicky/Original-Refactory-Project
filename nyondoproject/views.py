
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages



def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if username == "admin" and password == "admin123":
            return redirect("dashboard")
        else:
            # Add error message for invalid credentials
            messages.error(request, 'Invalid username or password')
            return redirect("login")
    return render(request, "login.html")

def logout(request):
    return render(request, 'logout.html')


def sign_page(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'sign_up.html', {'form': form})



       
           
    