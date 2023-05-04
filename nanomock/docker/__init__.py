from .interface import DockerInterface
from .linux import LinuxDockerInterface
from .windows import WindowsDockerInterface
from .macos import MacDockerInterface
from typing import Type
import platform


def create_docker_interface(compose_path: str,
                            project_name: str) -> DockerInterface:
    os_name = platform.system()

    if os_name == "Windows":
        return WindowsDockerInterface(compose_path, project_name)
    elif os_name == "Linux":
        return LinuxDockerInterface(compose_path, project_name)
    elif os_name == "Darwin":
        return MacDockerInterface(compose_path, project_name)
    else:
        raise NotImplementedError("Unsupported OS")


def get_docker_interface_class() -> Type[DockerInterface]:
    os_name = platform.system()

    if os_name == "Windows":
        return WindowsDockerInterface
    elif os_name == "Linux":
        return LinuxDockerInterface
    elif os_name == "Darwin":
        return MacDockerInterface
    else:
        raise NotImplementedError("Unsupported OS")