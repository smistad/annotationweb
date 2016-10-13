from django.conf.urls import url

from . import views

app_name = 'segmentation'
urlpatterns = [
    url(r'^segment-image/(?P<task_id>[0-9]+)/$', views.segment_image, name='segment_image'),
    url(r'^save/$', views.save_segmentation, name='save'),
]