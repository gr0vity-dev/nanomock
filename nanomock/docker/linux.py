from .interface import DockerInterface
from .mixin import DockerMixin
import subprocess


class LinuxDockerInterface(DockerMixin, DockerInterface):

    @classmethod
    def get_docker_gateway_ip(cls) -> str:
        command = "ifconfig | grep -A1 'docker' | grep inet | awk '{print $2}'"
        output = subprocess.check_output(command, shell=True, text=True)
        return output.strip()
