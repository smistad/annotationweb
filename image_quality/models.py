from django.db import models
from annotationweb.models import Task, KeyFrameAnnotation


class ImageQualityTask(models.Model):
    task = models.ManyToManyField(Task)
    name = models.CharField(max_length=255)
    image = models.ImageField()


class Rank(models.Model):
    index = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=128, default='') # Hex code color or css color name

    def __str__(self):
        return self.name


class Category(models.Model):
    iq_task = models.ForeignKey(ImageQualityTask, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    image_position_x = models.PositiveIntegerField(default=0)
    image_position_y = models.PositiveIntegerField(default=0)
    rankings = models.ManyToManyField(Rank)
    placeholder_text = models.CharField(max_length=255, default='')
    default_rank = models.ForeignKey(Rank, blank=True, null=True, on_delete=models.CASCADE, related_name='default_rank') # If this is set, it will be the rank select by default

    def __str__(self):
        return self.name


class Ranking(models.Model):
    annotation = models.ForeignKey(KeyFrameAnnotation, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    selection = models.ForeignKey(Rank, on_delete=models.CASCADE)