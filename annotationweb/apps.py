from django.apps import AppConfig


class AnnotationwebConfig(AppConfig):
    name = 'annotationweb'
    SITE_NAME = 'Annotation Web'
    # Annotation Web version
    VERSION_MAJOR = 2
    VERSION_MINOR = 0
    VERSION_PATCH = 0
    VERSION = f'{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}'
