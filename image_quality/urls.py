from django.urls import path
from . import views

app_name = 'image_quality'
urlpatterns = [
    path('rank-image/<int:task_id>/', views.rank_next_image, name='rank_image'),
    path('rank-image/<int:task_id>/<int:image_id>/', views.rank_image, name='rank_image'),
    path('show/<int:task_id>/<int:image_id>/', views.show, name='show_ranking'),
    path('save/', views.save, name='save'),
]
