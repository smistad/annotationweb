from abc import ABC, abstractmethod

"""
Base class for post processing routines
"""
class PostProcessingMethod(ABC):
    @abstractmethod
    def post_process(self, input_image, source, filename: str):
        pass


"""
Contains a list of post processing routines
"""
class _PostProcessingManager():
    register = {}

    def add(self, name: str, method: PostProcessingMethod):
        self.register[name] = method

    def get(self, name:str):
        return self.register[name]


post_processing_register = _PostProcessingManager()