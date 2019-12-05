from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render
from django.contrib.auth import authenticate, login, views
from django_otp import devices_for_user
from django_otp.forms import OTPAuthenticationForm, OTPAuthenticationFormMixin

from django import forms


class CustomAuthForm(OTPAuthenticationFormMixin, AuthenticationForm):
    otp_device = forms.CharField(required=False, widget=forms.Select)
    otp_token = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    def clean(self):
        self.cleaned_data = super(CustomAuthForm, self).clean()
        user = self.get_user()
        # check if user has a otp device enabled, if not skip verifying with OTP
        nr_of_devices = 0
        for device in devices_for_user(user):
            nr_of_devices += 1
        if nr_of_devices > 0:
            self.clean_otp(self.get_user())

        return self.cleaned_data

def login(request):
    return views.LoginView.as_view(template_name='user/login.html', authentication_form=CustomAuthForm)(request)


def logout(request):
    return views.logout_then_login(request)
