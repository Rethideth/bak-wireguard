from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name = 'home'),
    path('login/', auth_views.LoginView.as_view(), name= 'login'),
    path('logout/', auth_views.LogoutView.as_view(), name = 'logout'),
    path('register/', views.register, name='register'),
    path('mykeys/', views.mykeys, name = 'mykeys'),
    path('confajax/', views.getconfajax, name = 'confajax'),
    path('key/new', views.newkey, name = 'newkey'),
    path('key/delete/<int:key>/',views.deletekey,name='deletekey'),
    path('key/updatename/', views.updatekeyname, name='updatekeyname'),
    path('logs/', views.viewlogs, name = 'logs'),
    path('dbdown/', views.dbdown, name='dbdown'),
    
]
    
