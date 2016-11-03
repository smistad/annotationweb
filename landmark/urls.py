from django.conf.urls import url

from . import views

app_name = 'landmark'
urlpatterns = [
    url(r'^process/(?P<task_id>[0-9]+)/$', views.process_next_image, name='process_image'),
    url(r'^process/(?P<task_id>[0-9]+)/(?P<image_id>[0-9]+)/$', views.process_image, name='process_image'),
    url(r'^save/$', views.save, name='save'),
]
