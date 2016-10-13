from django.db import models
from classification.models import *


class SegmentedImage(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

