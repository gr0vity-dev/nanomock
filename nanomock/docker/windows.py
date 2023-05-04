from .interface import DockerInterface
from .mixin import DockerMixin
import subprocess


class WindowsDockerInterface(DockerMixin, DockerInterface):

    @classmethod
    def get_docker_gateway_ip(cls) -> str:
        command = "ipconfig | findstr /C:'Docker' /A:1 | findstr /C:'IPv4'"
        output = subprocess.check_output(command, shell=True, text=True)
        return output.strip().split()[-1]