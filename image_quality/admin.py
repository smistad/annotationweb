from django.contrib import admin
from image_quality.models import ImageQualityTask, Rank, Category, Ranking

admin.site.register(ImageQualityTask)
admin.site.register(Rank)
admin.site.register(Category)
admin.site.register(Ranking)
