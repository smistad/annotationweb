from django.apps import AppConfig
from common.config import TaskConfig


class LandmarkConfig(AppConfig, TaskConfig):
    name = 'landmark'

    @property
    def task_name(self):
        return 'Landmark'
