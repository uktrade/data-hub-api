from django.conf import settings
from django.utils.module_loading import import_string


class ProcessorManager:
    """
    """

    def __init__(self):
        self.processors = []
        for processor_class_path in settings.EMAIL_PROCESSOR_CLASSES:
            processor_class = import_string(processor_class_path)
            self.processors.append(processor_class())

    def process_email(self, message):
        for processor in self.processors:
            processed, message = processor.process_email(message)
            if not processed:
                continue
            break


processor_manager = ProcessorManager()
