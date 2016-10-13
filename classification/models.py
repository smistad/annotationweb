from django.db import models
from annotationweb.models import *


class ClassifiedImage(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    #user = models.ForeignKey() # Add user here eventually
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.image.filename + ' with label ' + self.label.name + ' created on ' + self.date.strftime('%Y-%m-%d %H:%M')



