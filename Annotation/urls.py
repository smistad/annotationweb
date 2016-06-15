from django.conf.urls import url

from . import views

app_name = 'annotation'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^datasets/$', views.datasets, name='datasets'),
    url(r'^add-image-sequence/(?P<dataset_id>[0-9]+)/$', views.add_image_sequence, name='add_image_sequence'),
    url(r'^add-key-frames/(?P<image_sequence_id>[0-9]+)/$', views.add_key_frames, name='add_key_frames'),
    url(r'^show_frame/(?P<image_sequence_id>[0-9]+)/(?P<frame_nr>[0-9]+)/$', views.show_frame, name='show_frame'),
    url(r'^new-dataset/$', views.new_dataset, name='new_dataset'),
    url(r'^delete-dataset/(?P<task_id>[0-9]+)/$', views.delete_dataset, name='delete_dataset'),
    url(r'^import-local-dataset/$', views.import_local_dataset, name='import_local_dataset'),
    url(r'^export-labeled-dataset/(?P<task_id>[0-9]+)/$', views.export_labeled_dataset, name='export_labeled_dataset'),
    url(r'^label-image/(?P<task_id>[0-9]+)/$', views.label_images, name='label_image'),
    url(r'^delete-task/(?P<task_id>[0-9]+)/$', views.delete_task, name='delete_task'),
    url(r'^undo-image-label/(?P<task_id>[0-9]+)/$', views.undo_image_label, name='undo_image_label'),
    url(r'^show-image/(?P<image_id>[0-9]+)/$', views.show_image, name='show_image'),
    url(r'^new-task/$', views.new_task, name='new_task'),
]