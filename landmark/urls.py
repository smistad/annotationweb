from django.urls import path

from . import views

app_name = 'landmark'
urlpatterns = [
    path('process/<int:task_id>/', views.process_next_image, name='process_image'),
    path('process/<int:task_id>/<int:image_id>/', views.process_image, name='process_image'),
    path('save/', views.save, name='save'),
]
