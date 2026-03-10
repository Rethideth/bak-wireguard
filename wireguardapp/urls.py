from django.urls import path
from . import views,ajax

from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name = 'home'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('mykeys/', views.mykeys, name='mykeys'),
    path('confajax/', ajax.getconfajax, name = 'confajax'),
    path('key/new', views.newkey, name = 'newkey'),
    path('key/delete/',ajax.deletekey,name='deletekey'),
    path('key/updatename/', ajax.updatekeyname, name='updatekeyname'),
    path('logs/', views.viewlogs, name = 'logs'),
    path('dbdown/', views.dbdown, name='dbdown'),
    path('server/all/', views.serverinterfaces, name='allservers'),
    path('server/<int:id>/', views.serverinterface, name='server'),
    path('server/toggle/', ajax.toggleServer,name='toggleserver'),
    path('server/state/',ajax.getpeerstate,name='peerstate'),
    path('server/new/', views.newinterface,name='newinterface'),
    path('server/delete/', views.deleteinterface,name='deleteinterface'),
    path('server/alter/<int:id>/',views.alterserver,name='alterserver'),
    path('downland/conf/',views.downlandConf, name='downlandconf'),
    path('users/', views.listusers, name='listusers'),
    path('users/verification/',ajax.verifyUser, name='verify'),
    path('users/new/', views.newuser, name='newuser'),
    path('users/delete/', views.deleteuser, name='deleteuser'),
    path('user/profile/<int:id>',views.userprofile,name='userprofile'),
    path('test/',views.test)
]
    
