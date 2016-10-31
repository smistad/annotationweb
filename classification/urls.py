from django.conf.urls import url

from . import views

app_name = 'classification'
urlpatterns = [
    url(r'^label-image/(?P<task_id>[0-9]+)/$', views.label_next_image, name='label_image'),
    url(r'^label-image/(?P<task_id>[0-9]+)/(?P<image_id>[0-9]+)/$', views.label_image, name='label_image'),
]