from django.urls import path
from . import views

app_name = 'caliper'
urlpatterns = [
    path('measure/<int:task_id>/', views.next_image, name='measure_image'),
    path('measure/<int:task_id>/<int:image_id>/', views.measure_image, name='measure_image'),
    path('show/<int:task_id>/<int:image_id>/', views.show, name='show'),
    path('spacing/<int:image_sequence_id>/', views.get_spacing, name='get_spacing'),
    path('save/', views.save, name='save'),
]
