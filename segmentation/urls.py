from django.conf.urls import url

from . import views

app_name = 'segmentation'
urlpatterns = [
    url(r'^segment-image/(?P<task_id>[0-9]+)/$', views.segment_next_image, name='segment_image'),
    url(r'^segment-image/(?P<task_id>[0-9]+)/(?P<image_id>[0-9]+)/$', views.segment_image, name='segment_image'),
    url(r'^show/(?P<task_id>[0-9]+)/(?P<image_id>[0-9]+)/$', views.show_segmentation, name='show_segmentation'),
    url(r'^save/$', views.save_segmentation, name='save'),
]