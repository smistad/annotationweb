from django.urls import path
from . import views

app_name = 'spline_segmentation'
urlpatterns = [
    path('segment-image/<int:task_id>/', views.segment_next_image, name='annotate'),
    path('segment-image/<int:task_id>/<int:image_id>/', views.segment_image, name='annotate'),
    path('save/', views.save_segmentation, name='save'),
]
