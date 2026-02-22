from django.shortcuts import redirect
from django.db import connections
from django.db.utils import OperationalError
from django.urls import reverse

ALLOWED_PATHS = [
    reverse('dbdown'),
    '/',
]

class DatabaseCheckMiddleware:
    """
    Middleware for checking database connection.

    If down, users cannot access any sites that require database access, e.g. login page, mykeys page,...
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            connections['default'].cursor()
        except OperationalError:
            if request.path not in ALLOWED_PATHS:
                return redirect('dbdown')

        return self.get_response(request)