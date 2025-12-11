from typing import Dict
from annotationweb.serialization import SerializationObject, Serialization, KeyFrameAnnotation, Label
from annotationweb.models import KeyFrameAnnotation as KeyFrameAnnotationModel
from landmark.models import Landmark as LandmarkModel


def serialize(serialization:Serialization, key_frame_model:KeyFrameAnnotationModel, key_frame:KeyFrameAnnotation, label_mapping:Dict[int, Label]):
    serialization_objects = []
    for point in LandmarkModel.objects.filter(image=key_frame_model):
        serialization_objects.append(Landmark(serialization, point.x, point.y, label_mapping[point.label.id], key_frame))
    return serialization_objects


class Landmark(SerializationObject):
    counter = 1

    def __init__(self, serialization:Serialization, x:float, y:float, label:Label, image:KeyFrameAnnotation):
        super().__init__(serialization, Landmark.counter)
        Landmark.counter += 1
        serialization.add({
            'model': 'landmark.landmark',
            'pk': f'$landmark$landmark${self.id}$',
            'fields': {
                'image': f'$annotationweb$keyframeannotation${image.id}$',
                'label': f'$annotationweb$label${label.id}$',
                'x': x,
                'y': y,
            },
        })