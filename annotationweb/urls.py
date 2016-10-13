"""annotationweb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from . import views

app_name = 'annotationweb'
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
    url(r'^delete-task/(?P<task_id>[0-9]+)/$', views.delete_task, name='delete_task'),
    url(r'^show-image/(?P<image_id>[0-9]+)/$', views.show_image, name='show_image'),
    url(r'^new-task/$', views.new_task, name='new_task'),

    url(r'^admin/', admin.site.urls),
    url(r'^user/', include('user.urls')),
    url(r'^classification/', include('classification.urls')),
    url(r'^segmentation/', include('segmentation.urls')),
    url(r'^boundingbox/', include('boundingbox.urls')),
]

# This is for making statics in a development environment
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()