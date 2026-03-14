from django.urls import path
from . import views,ajax

from django.contrib.auth import views as auth_views
from wireguardapp.forms import CustomLoginView

urlpatterns = [
    path('', views.home, name = 'home'),
    path("login/", CustomLoginView.as_view(), name="login"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('mykeys/', views.mykeys, name='mykeys'),
    path('confajax/', ajax.getconfajax, name = 'confajax'),
    path('key/new', views.newkey, name = 'newkey'),
    path('key/delete/',ajax.deletekey,name='deletekey'),
    path('key/updatename/', ajax.updatekeyname, name='updatekeyname'),
    path('dbdown/', views.dbdown, name='dbdown'),
    path('server/all/', views.serverinterfaces, name='allservers'),
    path('server/<int:id>/', views.serverinterface, name='server'),
    path('server/toggle/', ajax.toggleServer,name='toggleserver'),
    path('server/state/',ajax.getpeerstate,name='peerstate'),
    path('server/delete/', views.deleteinterface,name='deleteinterface'),
    path("server/add/", views.serverinterfaceform, name="newinterface"),
    path("server/<int:id>/edit/", views.serverinterfaceform, name="editinterface"),
    path('downland/conf/',views.downlandConf, name='downlandconf'),
    path('users/', views.listusers, name='listusers'),
    path('users/verification/',ajax.verifyUser, name='verify'),
    path('users/new/', views.newuser, name='newuser'),
    path('user/profile/<int:id>',views.usersettings,name='usersettings'),
    path('user/keys/<int:id>',views.userkeys,name='userkeys'),
    path('help/', views.help, name='help'),
    path('test/',views.test)
]
    
