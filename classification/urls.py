from django.conf.urls import url

from . import views

app_name = 'classification'
urlpatterns = [
    url(r'^label-image/(?P<task_id>[0-9]+)/$', views.label_images, name='label_image'),
    url(r'^undo-image-label/(?P<task_id>[0-9]+)/$', views.undo_image_label, name='undo_image_label'),
    url(r'^export-labeled-dataset/(?P<task_id>[0-9]+)/$', views.export_labeled_dataset, name='export_labeled_dataset'),
]