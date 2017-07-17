from django.conf.urls import url

from . import views

app_name = 'cardiac'
urlpatterns = [
    url(r'^segmentation/(?P<task_id>[0-9]+)/$', views.segment_next_image, name='segment_image'),
    url(r'^segmentation/(?P<task_id>[0-9]+)/(?P<image_id>[0-9]+)/$', views.segment_image, name='segment_image'),
    url(r'^segmentation/show/(?P<task_id>[0-9]+)/(?P<image_id>[0-9]+)/$', views.show_segmentation, name='show_segmentation'),
    url(r'^segmentation/save/$', views.save_segmentation, name='save'),
]