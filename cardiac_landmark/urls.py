from django.urls import path

from . import views

app_name = 'cardiac_landmark'
urlpatterns = [
    path('cardiac_landmark/<int:task_id>/', views.landmark_next_image, name='landmark_image'),
    path('cardiac_landmark/<int:task_id>/<int:image_id>/', views.landmark_image, name='landmark_image'),
    path('cardiac_landmark/show/<int:task_id>/<int:image_id>/', views.show_landmarks, name='show_landmarks'),
    path('cardiac_landmark/save/', views.save_landmark, name='save'),
]
