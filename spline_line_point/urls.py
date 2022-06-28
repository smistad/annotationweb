from django.urls import path
from . import views

app_name = 'spline_line_point'
urlpatterns = [
    path('segment-image/<int:task_id>/', views.segment_next_image, name='segment_image'),
    path('segment-image/<int:task_id>/<int:image_id>/', views.segment_image, name='segment_image'),
    path('show/<int:task_id>/<int:image_id>/', views.show_segmentation, name='show_segmentation'),
    path('save/', views.save_segmentation, name='save'),
]
