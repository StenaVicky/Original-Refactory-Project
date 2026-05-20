"""
URL configuration for salesproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path,include
from django.contrib import admin
from . import views
from django.contrib.auth import views as auth_views




urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.login_view, name="login_view"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("saleapp/", include("saleapp.urls")),
    path("stockapp/", include("stockapp.urls")),
    path("schemeapp/",include("schemeapp.urls")),
    path('logout/', views.logout, name='logout'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('signup/', views.sign_page, name='sign_up'),
    path('login/', views.login_view, name='login')
]
    
    
