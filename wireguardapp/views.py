from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from django.core.exceptions import PermissionDenied

from .forms import CustomUserCreationForm
# Create your views here.

def home(request):
    return render(request, 'wireguardapp/main.html')

@login_required
def test(request):
    return render(request, 'wireguardapp/test.html')

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # auto-login after registration
            return redirect('/')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

@login_required
def mykeys(request):
    return render(request, 'wireguard/mykeys.html')


def viewlogs(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_superuser:
        raise PermissionDenied
    return render(request, 'wireguardapp/logs.html')