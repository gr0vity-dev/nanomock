from abc import ABC, abstractmethod
from typing import List, Optional


class DockerInterface(ABC):

    def __init__(self, compose_path: str, project_name: str):
        self.compose_path = compose_path
        self.project_name = project_name

    @classmethod
    @abstractmethod
    def get_docker_gateway_ip(cls) -> str:
        pass

    @abstractmethod
    def stop_and_remove_container(self, container_name: str, force_stop=True):
        pass

    @abstractmethod
    def check_container_running(self, container_name: str):
        pass

    @abstractmethod
    def compose_start(self, nodes: Optional[List[str]] = None):
        pass

    @abstractmethod
    def compose_restart(self, nodes: Optional[List[str]] = None):
        pass

    @abstractmethod
    def compose_stop(self, nodes: Optional[List[str]] = None):
        pass

    @abstractmethod
    def compose_down(self, nodes: Optional[List[str]] = None):
        pass

    @abstractmethod
    def compose_build(self):
        pass

    @abstractmethod
    def compose_pull(self):
        pass

    @abstractmethod
    def container_count(self, container_names):
        pass

    @abstractmethod
    def create_network(self, network_name):
        pass

    @abstractmethod
    def get_network_gateway(self, network_name):
        pass
