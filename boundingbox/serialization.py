from typing import Dict
from annotationweb.serialization import SerializationObject, Serialization, KeyFrameAnnotation, Label
from annotationweb.models import KeyFrameAnnotation as KeyFrameAnnotationModel
from boundingbox.models import BoundingBox as BoundingBoxModel


def serialize(serialization:Serialization, key_frame_model:KeyFrameAnnotationModel, key_frame:KeyFrameAnnotation, label_mapping:Dict[int, Label]):
    serialization_objects = []
    for box in BoundingBoxModel.objects.filter(image=key_frame_model):
        serialization_objects.append(BoundingBox(serialization, box.x, box.y, box.width, box.height, label_mapping[box.label.id], key_frame))
    return serialization_objects


class BoundingBox(SerializationObject):
    counter = 1

    def __init__(self, serialization:Serialization, x:int, y:int, width:int, height:int, label:Label, image:KeyFrameAnnotation):
        super().__init__(serialization, BoundingBox)
        serialization.add({
            'model': 'boundingbox.boundingbox',
            'pk': f'$boundingbox$boundingbox${self.id}$',
            'fields': {
                'image': f'$annotationweb$keyframeannotation${image.id}$',
                'label': f'$annotationweb$label${label.id}$',
                'x': x,
                'y': y,
                'width': width,
                'height': height,
            },
        })