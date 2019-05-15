from django.urls import path

from . import views

app_name = 'classification'
urlpatterns = [
    path('label-image/<int:task_id>/', views.label_next_image, name='label_image'),
    path('label-image/<int:task_id>/<int:image_id>/', views.label_image, name='label_image'),
    path('save/', views.save_labels, name='save')
]