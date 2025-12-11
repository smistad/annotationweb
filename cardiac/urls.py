from django.urls import path

from . import views

app_name = 'cardiac'
urlpatterns = [
    path('segmentation/<int:task_id>/', views.segment_next_image, name='annotate'),
    path('segmentation/<int:task_id>/<int:image_id>/', views.segment_image, name='annotate'),
    path('segmentation/save/', views.save_segmentation, name='save'),
]