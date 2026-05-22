from . import views
from django.urls import path
from django.contrib.auth import views as auth_views


urlpatterns =[
    # path('logout/', views.logout, name='logout'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    # path('signup/', views.sign_page, name='sign_up'),
    # path('login/', views.login_view, name='login'),
    # path("", views.login_view, name="login_view"),
]