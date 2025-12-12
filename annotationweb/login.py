from django.http import HttpResponseRedirect
from django.conf import settings
from re import compile
from django.contrib.auth import logout
from django.contrib import messages
from django_otp import devices_for_user

EXEMPT_URLS = [compile(settings.LOGIN_URL.lstrip('/'))]
if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
    EXEMPT_URLS += [compile(expr) for expr in settings.LOGIN_EXEMPT_URLS]

from django.utils.deprecation import MiddlewareMixin

class LoginRequiredMiddleware(MiddlewareMixin):
    """
    Middleware that requires a user to be authenticated to view any page other
    than LOGIN_URL. Exemptions to this requirement can optionally be specified
    in settings via a list of regular expressions in LOGIN_EXEMPT_URLS (which
    you can copy from your urls.py).
    """
    def process_request(self, request):
        assert hasattr(request, 'user'), """
        The Login Required middleware needs to be after AuthenticationMiddleware.
        Also make sure to include the template context_processor:
        'django.contrib.auth.context_processors.auth'."""
        if not request.user.is_authenticated:
            path = request.path_info.lstrip('/')
            if not any(m.match(path) for m in EXEMPT_URLS):
                return HttpResponseRedirect(settings.LOGIN_URL)
        else:
            if settings.REQUIRE_2FA_FOR_ALL_USERS:
                nr_of_devices = len(list(devices_for_user(request.user)))
                if nr_of_devices == 0:
                    messages.error(request, 'This site requires 2FA. You have no 2FA configured.')
                    logout(request)
                    return HttpResponseRedirect('')
