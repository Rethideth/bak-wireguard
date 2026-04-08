from django.urls import path
from . import views,ajax

from django.contrib.auth import views as auth_views
from wireguardapp.forms import CustomLoginView,BootstrapPasswordResetForm,BootstrapSetPasswordForm

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name = 'home'),
    path("login/", CustomLoginView.as_view(), name="login"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('mykeys/', views.mykeys, name='mykeys'),
    path('confajax/', ajax.getconfajax, name = 'confajax'),
    path('key/new/', views.newkey, name = 'newkey'),
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
    path('test/',views.test),
    path("users/filter/", ajax.filterUsers, name="filterusers"),
    path("peers/filter/", ajax.filterPeers, name="filterpeers"),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/passwordresetform.html',
        form_class=BootstrapPasswordResetForm,
        email_template_name='registration/passwordresetemail.html',
        subject_template_name='registration/passwordresetemailsubject.txt'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/passwordresetdone.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/passwordresetconfirm.html',
        form_class=BootstrapSetPasswordForm), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/passwordresetcomplete.html'), name='password_reset_complete'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
