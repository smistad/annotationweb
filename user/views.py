from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, views, logout
from django_otp import devices_for_user
from django_otp.forms import OTPAuthenticationForm, OTPAuthenticationFormMixin
from django.conf import settings
from django import forms
from django_otp.views import LoginView as OTPLoginView


class CustomAuthForm(OTPAuthenticationFormMixin, AuthenticationForm):
    otp_device = forms.CharField(required=False, widget=forms.Select)
    otp_token = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    def clean(self):
        self.cleaned_data = super(CustomAuthForm, self).clean()
        user = self.get_user()
        # check if user has a otp device enabled, if not skip verifying with OTP
        nr_of_devices = len(list(devices_for_user(user)))
        if nr_of_devices > 0:
            self.clean_otp(self.get_user())

        return self.cleaned_data


def login(request):
    if settings.REQUIRE_2FA_FOR_ALL_USERS:
        return OTPLoginView.as_view(template_name='user/login.html')(request)
    else:
        return views.LoginView.as_view(template_name='user/login.html', authentication_form=CustomAuthForm)(request)


def logout_view(request):
    logout(request)
    return redirect('index')
