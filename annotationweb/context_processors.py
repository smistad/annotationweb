from django.apps import apps


def global_variables(request):
    app_config = apps.get_app_config('annotationweb')
    return {
        'VERSION': app_config.VERSION,
        'SITE_NAME': app_config.SITE_NAME
    }