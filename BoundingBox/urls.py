from django.conf.urls import url

from . import views

app_name = 'boundingbox'
urlpatterns = [
    url(r'^new-task/$', views.new_task, name='new_task'),
    url(r'^delete-task/(?P<task_id>[0-9]+)/$', views.delete_task, name='delete_task'),
    url(r'^process/(?P<task_id>[0-9]+)/$', views.process_image, name='process_image'),
    url(r'^save/$', views.save_boxes, name='save'),
    url(r'^export/(?P<task_id>[0-9]+)/$', views.export, name='export'),

]
