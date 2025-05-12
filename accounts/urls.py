# urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import PaddieLoginForm 

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', 
         auth_views.LoginView.as_view(
             template_name='accounts/login.html',
             form_class=PaddieLoginForm, 
             redirect_authenticated_user=True
         ), 
         name='login'),
    path('logout/', views.custom_logout, name='logout'),  # Use custom logout view
    path('profile/', views.profile, name='profile'),
    path('whatsapp-groups/', views.whatsapp_groups, name='whatsapp_groups'),
    path('join-whatsapp-group/', views.join_whatsapp_group, name='join_whatsapp_group'),
]