from django.db import models
from django.contrib.auth.models import User


class Dataset(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Subject(models.Model):
    name = models.CharField(max_length=200, help_text='Use anonymized id')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)

    def __str__(self):
        return self.dataset.name + ' - ' + self.name

    class Meta:
        ordering = ['dataset__name', 'name']


class Label(models.Model):
    name = models.CharField(max_length=200)

    # Color stored as R G B with values from 0 to 255
    color_red = models.PositiveSmallIntegerField(default=255)
    color_green = models.PositiveSmallIntegerField(default=0)
    color_blue = models.PositiveSmallIntegerField(default=0)

    parent = models.ForeignKey('Label', blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Task(models.Model):
    CLASSIFICATION = 'classification'
    BOUNDING_BOX = 'boundingbox'
    LANDMARK = 'landmark'
    CARDIAC_SEGMENTATION = 'cardiac_segmentation'
    CARDIAC_PLAX_SEGMENTATION = 'cardiac_plax_segmentation'
    CARDIAC_ALAX_SEGMENTATION = 'cardiac_alax_segmentation'
    IMAGE_QUALITY = 'image_quality'
    SPLINE_SEGMENTATION = 'spline_segmentation'
    SPLINE_LINE_POINT = 'spline_line_point'
    CALIPER = 'caliper'
    TASK_TYPES = (
        (CLASSIFICATION, 'Classification'),
        (BOUNDING_BOX, 'Bounding box'),
        (LANDMARK, 'Landmark'),
        (CARDIAC_SEGMENTATION, 'Cardiac apical segmentation'),
        (CARDIAC_PLAX_SEGMENTATION, 'Cardiac PLAX segmentation'),
        (CARDIAC_ALAX_SEGMENTATION, 'Cardiac ALAX segmentation'),
        (SPLINE_SEGMENTATION, 'Spline segmentation'),
        (SPLINE_LINE_POINT, 'Splines, lines & point segmentation'),
        (IMAGE_QUALITY, 'Image Quality'),
        (CALIPER, 'Caliper'),
    )

    CLASSIFICATION_WHOLE_SEQUENCE = 'whole_sequence'
    CLASSIFICATION_SINGLE_FRAME = 'single_frame'
    # CLASSIFICATION_SUBSEQUENCE = 'subsequence'
    CLASSIFICATION_TYPES = (
        (CLASSIFICATION_WHOLE_SEQUENCE, 'Whole sequence'),
        (CLASSIFICATION_SINGLE_FRAME, 'Single frame'),
        # (CLASSIFICATION_SUBSEQUENCE, 'Subsequence'),
    )

    name = models.CharField(max_length=200)
    dataset = models.ManyToManyField(Dataset)
    show_entire_sequence = models.BooleanField(help_text='Allow user to see entire sequence.', default=False)
    frames_before = models.PositiveIntegerField(help_text='How many frames to allow user to see before a key frame', default=0)
    frames_after = models.PositiveIntegerField(help_text='How many frames to allow user to see after a key frame', default=0)
    auto_play = models.BooleanField(help_text='Auto play image sequences', default=True)
    shuffle_videos = models.BooleanField(help_text='Shuffle videos for annotation task', default=True)
    user_frame_selection = models.BooleanField(help_text='Annotaters can select which frames to annotate in a video', default=False)
    annotate_single_frame = models.BooleanField(help_text='Annotate a single frame at a time in videos', default=True)
    type = models.CharField(max_length=50, choices=TASK_TYPES)
    label = models.ManyToManyField(Label,
           help_text='<button onclick="'
                     'window.open(\'/new-label/\', \'Add new label\', \'width=400,height=400,scrollbars=no\');"'
                     ' type="button">Add new label</button>')
    user = models.ManyToManyField(User)
    description = models.TextField(default='', blank=True)
    large_image_layout = models.BooleanField(default=False, help_text='Use a large image layout for annotation')
    post_processing_method = models.CharField(default='', help_text='Name of post processing method to use', max_length=255, blank=True)

    classification_type = models.CharField(max_length=50, blank=True, choices=CLASSIFICATION_TYPES)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    @property
    def total_number_of_images(self):
        if self.user_frame_selection_valid():
            return ImageSequence.objects.filter(subject__dataset__task=self).count()
        elif (self.type == Task.CLASSIFICATION
              and (self.classification_type == Task.CLASSIFICATION_WHOLE_SEQUENCE
                   # or self.classification_type == Task.CLASSIFICATION_SUBSEQUENCE
                   or (self.classification_type == Task.CLASSIFICATION_SINGLE_FRAME and not self.user_frame_selection))
              ):
            return ImageSequence.objects.filter(subject__dataset__task=self).count()
        else:
            return ImageSequence.objects.filter(imageannotation__task=self).count()

    @property
    def number_of_annotated_images(self):
        return ImageSequence.objects.filter(imageannotation__in=ImageAnnotation.objects.filter(task=self, finished=True)).count()

    @property
    def percentage_finished(self):
        if self.total_number_of_images == 0:
            return 0
        else:
            return round(self.number_of_annotated_images*100 / self.total_number_of_images, 1)

    def user_frame_selection_valid(self):
        if (self.type == Task.CLASSIFICATION
            and (self.classification_type == Task.CLASSIFICATION_WHOLE_SEQUENCE
                 # or self.classification_type == Task.CLASSIFICATION_SUBSEQUENCE
                 )):
            return False

        return True


class ImageSequence(models.Model):
    format = models.CharField(max_length=1024, help_text='Should contain # which will be replaced with an integer, '
                                                         'increasing with 1 for each frame. E.g. /path/to/frame_#.png')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    nr_of_frames = models.PositiveIntegerField()
    start_frame_nr = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.format


class ImageAnnotation(models.Model):
    """
    Represents an annotation of an entire image sequence
    """

    image = models.ForeignKey(ImageSequence, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    QUALITY_POOR = 'poor'
    QUALITY_OK = 'ok'
    QUALITY_GOOD = 'good'
    IMAGE_QUALITY_CHOICES = (
        (QUALITY_POOR, 'Poor'),
        (QUALITY_OK, 'OK'),
        (QUALITY_GOOD, 'Good'),
    )
    image_quality = models.CharField(max_length=50, choices=IMAGE_QUALITY_CHOICES)
    comments = models.TextField()
    rejected = models.BooleanField()
    finished = models.BooleanField(default=True)


class KeyFrameAnnotation(models.Model):
    """
    Represents an annotation of a frame of an image_sequence
    """

    frame_nr = models.PositiveIntegerField()
    image_annotation = models.ForeignKey(ImageAnnotation, on_delete=models.CASCADE)
    frame_metadata = models.CharField(default='', max_length=512, help_text='A text field for storing arbitrary metadata on the current frame')

    def __str__(self):
        return str(self.frame_nr)


# Used to attach metadata to images, such as acquisition parameters
class ImageMetadata(models.Model):
    image = models.ForeignKey(ImageSequence, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=256)

    def __str__(self):
        return self.name + ': ' + self.value
