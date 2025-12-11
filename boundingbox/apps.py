from django.apps import AppConfig
from common.config import TaskConfig


class BoundingboxConfig(AppConfig, TaskConfig):
    name = 'boundingbox'

    @property
    def task_name(self):
        return 'Bounding Box'

