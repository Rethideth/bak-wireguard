from django.urls import path
from .views import home, test, register
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', home, name = 'home'),
    path('test/', test, name = 'test'),
    path('login/', auth_views.LoginView.as_view(), name= 'login'),
    path('logout/', auth_views.LogoutView.as_view(), name = 'logout'),
    path('register/', register, name='register'),

    
]
    
