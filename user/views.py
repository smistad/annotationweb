from django.shortcuts import render
from django.contrib.auth import authenticate, login, views
from django_otp.forms import OTPAuthenticationForm


def login(request):
    return views.LoginView.as_view(template_name='user/login.html', authentication_form=OTPAuthenticationForm)(request)


def logout(request):
    return views.logout_then_login(request)
