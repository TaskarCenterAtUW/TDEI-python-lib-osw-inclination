import os
from typing import ClassVar
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class EventBusSettings:
    connection_string: str = os.environ.get('QUEUECONNECTION', None)
    request_topic: str = os.environ.get('REQUEST_TOPIC', None)
    request_subscription: str = os.environ.get('REQUEST_SUBSCRIPTION', None)
    response_topic: str = os.environ.get('RESPONSE_TOPIC', None)
    container_name: str = os.environ.get('CONTAINER_NAME', 'osw')


class Settings(BaseSettings):
    app_name: str = 'python-lib-osw-inclination'
    event_bus: ClassVar[EventBusSettings] = EventBusSettings()  # Annotate event_bus as a ClassVar
    max_concurrent_messages: int = int(os.environ.get('MAX_CONCURRENT_MESSAGES', 2))  # Convert to int

    def get_root_directory(self) -> str:
        return os.path.dirname(os.path.abspath(__file__))

    def get_download_directory(self) -> str:
        root_dir = self.get_root_directory()
        parent_dir = os.path.dirname(root_dir)
        return os.path.join(parent_dir, 'downloads')

