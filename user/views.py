from django.shortcuts import render
from django.contrib.auth import authenticate, login, views

# Create your views here.
def login(request):
    return views.login(request, template_name='user/login.html')

def logout(request):
    return views.logout_then_login(request)
