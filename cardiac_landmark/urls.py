from django.conf.urls import url

from . import views

app_name = 'cardiac_landmark'
urlpatterns = [
    url(r'^cardiac_landmark/(?P<task_id>[0-9]+)/$', views.landmark_next_image, name='landmark_image'),
    url(r'^cardiac_landmark/(?P<task_id>[0-9]+)/(?P<image_id>[0-9]+)/$', views.landmark_image, name='landmark_image'),
    url(r'^cardiac_landmark/show/(?P<task_id>[0-9]+)/(?P<image_id>[0-9]+)/$', views.show_landmarks, name='show_landmarks'),
    url(r'^cardiac_landmark/save/$', views.save_landmark, name='save'),
]
