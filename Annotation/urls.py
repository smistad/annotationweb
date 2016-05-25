from django.conf.urls import url

from . import views

app_name = 'annotation'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^import-local-dataset/$', views.import_local_dataset, name='import_local_dataset'),
    url(r'^export-labeled-dataset/$', views.export_labeled_dataset, name='export_labeled_dataset'),
    url(r'^label-image/(?P<task_id>[0-9]+)/$', views.label_images, name='label_image'),
    url(r'^show-image/(?P<image_id>[0-9]+)/$', views.show_image, name='show_image'),
]