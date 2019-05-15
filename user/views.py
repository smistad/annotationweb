from django.shortcuts import render
from django.contrib.auth import authenticate, login, views


def login(request):
    return views.LoginView.as_view(template_name='user/login.html')(request)


def logout(request):
    return views.logout_then_login(request)
