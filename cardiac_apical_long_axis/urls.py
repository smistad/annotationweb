from django.urls import path

from . import views

app_name = 'cardiac_apical_long_axis'
urlpatterns = [
    path('segmentation/<int:task_id>/', views.segment_next_image, name='segment_image'),
    path('segmentation/<int:task_id>/<int:image_id>/', views.segment_image, name='segment_image'),
    path('segmentation/show/<int:task_id>/<int:image_id>/', views.show_segmentation, name='show_segmentation'),
    path('segmentation/save/', views.save_segmentation, name='save'),
]