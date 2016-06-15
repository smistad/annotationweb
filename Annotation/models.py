from django.db import models

class Dataset(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Image(models.Model):
    filename = models.CharField(max_length=255)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)

    def __str__(self):
        return self.filename

class Task(models.Model):
    name = models.CharField(max_length = 200)
    dataset = models.ManyToManyField(Dataset)

    def __str__(self):
        return self.name

class Label(models.Model):
    name = models.CharField(max_length=200)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class LabeledImage(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE)
    #user = models.ForeignKey() # Add user here eventually
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.image.filename + ' with label ' + self.label.name + ' created on ' + self.date.strftime('%Y-%m-%d %H:%M')

class ImageSequence(models.Model):
    format = models.CharField(max_length=1024)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    nr_of_frames = models.PositiveIntegerField()

    def __str__(self):
        return self.format

class KeyFrame(models.Model):
    frame_nr = models.PositiveIntegerField()
    image_sequence = models.ForeignKey(ImageSequence, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.frame_nr)